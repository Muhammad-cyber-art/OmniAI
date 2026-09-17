"""
OmniLab AI - SimulationEngineService
Core simulation logic: session management, RAG context retrieval, AI scoring.
"""
import json
import logging
from typing import Dict, Any, Tuple
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.conf import settings

from apps.billing.models import UserQuotaUsage
from apps.billing.services import BillingService
from apps.curriculum.services import CurriculumService

logger = logging.getLogger(__name__)


# ─── Structured AI Response Schema ────────────────────────────────────────────
# The AI MUST return this exact JSON schema. Zero-tolerance for hallucination
# outside the knowledge base is enforced via system prompt constraints.

AI_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["feedback", "step_score", "next_scenario", "is_final", "error_flags", "strengths"],
    "properties": {
        "feedback": {"type": "string", "description": "Detailed feedback on the student's response."},
        "step_score": {"type": "number", "minimum": 0, "maximum": 100, "description": "Score for this step (0-100)."},
        "next_scenario": {"type": "string", "description": "Next scenario prompt, empty string if final."},
        "is_final": {"type": "boolean", "description": "True if the simulation should end after this step."},
        "error_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of error categories identified (e.g., 'logical_error', 'factual_error')."
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of strengths demonstrated."
        },
        "knowledge_gap": {"type": "string", "description": "Specific knowledge area where student needs improvement."},
    }
}

SYSTEM_PROMPT_TEMPLATE = """You are an expert AI evaluator for the OmniLab AI platform.
You are evaluating a {domain} simulation for the role: {role_context}

## Your Constraints (CRITICAL):
1. You MUST ONLY reference information from the provided KNOWLEDGE BASE CONTEXT below.
2. Do NOT introduce any facts, laws, formulas, or concepts that are NOT in the knowledge base.
3. If the student's answer cannot be evaluated from the knowledge base, say so explicitly.
4. You must return ONLY a valid JSON object matching the schema below. No other text.

## Knowledge Base Context:
{rag_context}

## Simulation Case:
{case_description}

## Grading Rubric:
{rubric}

## Response Schema (return EXACTLY this JSON):
{schema}

## Conversation so far:
{conversation_history}

## Student's latest response:
{student_input}

Evaluate strictly and return the JSON response now."""


class AIResponseParseError(Exception):
    pass


class SimulationEngineService:
    """
    Manages the full lifecycle of a simulation session.
    Enforces state machine transitions and zero-hallucination RAG grounding.
    """

    # ── Session Lifecycle ─────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def start_session(student, case_id: str) -> "SimulationSession":
        """
        Creates and activates a new simulation session.
        Steps:
        1. Validate case exists and is published.
        2. Check student quota via BillingService.
        3. Increment active_sessions_count.
        4. Create session in ACTIVE state.
        5. Decrement monthly_simulations quota.
        """
        from apps.simulation.models import SimulationCase, SimulationSession

        try:
            case = SimulationCase.objects.select_related(
                "course__domain", "lesson"
            ).get(id=case_id, is_published=True)
        except SimulationCase.DoesNotExist:
            raise ValueError(f"SimulationCase '{case_id}' not found or not published.")

        # Quota check
        can_start, reason = BillingService.can_start_simulation(student)
        if not can_start:
            raise PermissionError(reason)

        # Update quota counters atomically
        quota = UserQuotaUsage.objects.select_for_update().get(user=student)
        quota.monthly_simulations_used += 1
        quota.active_sessions_count += 1
        quota.save(update_fields=["monthly_simulations_used", "active_sessions_count", "updated_at"])

        # Create session
        session = SimulationSession.objects.create(
            student=student,
            case=case,
            status=SimulationSession.Status.ACTIVE,
            started_at=timezone.now(),
            current_step=0,
        )

        logger.info(
            "Session started: student=%s case=%s session=%s",
            student.email, case.title, session.id,
        )
        return session

    @staticmethod
    @transaction.atomic
    def process_turn(
        session_id: str,
        student,
        student_input: str,
    ) -> Dict[str, Any]:
        """
        Processes one student turn (action) in an active session.
        Steps:
        1. Load and lock session.
        2. Check daily AI turn quota.
        3. Retrieve RAG context.
        4. Build prompt and call AI.
        5. Parse and validate AI response.
        6. Log step and update session state.
        7. If final step → close session.
        Returns the full step log data dict.
        """
        from apps.simulation.models import SimulationSession, SimulationStepLog

        # Load and lock session
        try:
            session = SimulationSession.objects.select_for_update().select_related(
                "case__course__domain",
                "case__lesson",
            ).get(id=session_id, student=student)
        except SimulationSession.DoesNotExist:
            raise ValueError("Session not found.")

        if session.status != SimulationSession.Status.ACTIVE:
            raise PermissionError(
                f"Session is not active (status={session.status}). Cannot process turn."
            )

        # Daily AI turn quota check
        can_send, reason = BillingService.can_send_ai_turn(student)
        if not can_send:
            raise PermissionError(reason)

        # Check max steps
        next_step_number = session.steps_taken + 1
        is_final_by_steps = next_step_number >= session.case.max_steps

        # RAG: retrieve relevant chunks
        lesson_ids = [session.case.lesson_id] if session.case.lesson_id else []
        rag_results = []
        if lesson_ids:
            rag_results = CurriculumService.retrieve_relevant_chunks(
                query=student_input,
                lesson_ids=lesson_ids,
            )
        rag_context = "\n\n---\n\n".join([text for text, _ in rag_results]) or "No specific knowledge base context available."

        # Build conversation history from previous steps
        previous_steps = SimulationStepLog.objects.filter(
            session=session
        ).order_by("step_number").values("step_number", "student_input", "feedback_text", "next_scenario_text")

        conversation_history = ""
        for step in previous_steps:
            conversation_history += (
                f"\n[Step {step['step_number']}]\n"
                f"Student: {step['student_input']}\n"
                f"AI: {step['feedback_text']}\n"
                f"Next Prompt: {step['next_scenario_text']}\n"
            )

        # Call AI
        ai_response, prompt_tokens, completion_tokens = SimulationEngineService._call_ai(
            session=session,
            student_input=student_input,
            rag_context=rag_context,
            conversation_history=conversation_history,
            force_final=is_final_by_steps,
        )

        # Validate AI response
        step_score = float(ai_response.get("step_score", 0.0))
        step_score = max(0.0, min(100.0, step_score))
        is_final = bool(ai_response.get("is_final", False)) or is_final_by_steps
        feedback_text = ai_response.get("feedback", "")
        next_scenario = ai_response.get("next_scenario", "") if not is_final else ""
        error_flags = ai_response.get("error_flags", [])
        strengths = ai_response.get("strengths", [])

        # Update session score (running weighted average)
        old_total = session.total_score * session.steps_taken
        new_total = old_total + step_score
        session.steps_taken = next_step_number
        session.total_score = new_total / session.steps_taken
        session.current_step = next_step_number

        # Update error analysis
        error_analysis = session.error_analysis or {}
        for flag in error_flags:
            error_analysis[flag] = error_analysis.get(flag, 0) + 1
        session.error_analysis = error_analysis

        # Update quota: daily AI turns
        quota = UserQuotaUsage.objects.select_for_update().get(user=student)
        quota.daily_ai_turns_used += 1
        quota.save(update_fields=["daily_ai_turns_used", "updated_at"])

        # Create step log
        step_log = SimulationStepLog.objects.create(
            session=session,
            step_number=next_step_number,
            student_input=student_input,
            ai_response_raw=ai_response,
            step_score=step_score,
            feedback_text=feedback_text,
            next_scenario_text=next_scenario,
            is_final_step=is_final,
            rag_context_chunks=[text for text, _ in rag_results],
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # Close session if final
        if is_final:
            SimulationEngineService._close_session(session)
        else:
            session.save(update_fields=[
                "steps_taken", "total_score", "current_step", "error_analysis", "last_activity_at"
            ])

        logger.info(
            "Turn processed: session=%s step=%d score=%.1f is_final=%s",
            session.id, next_step_number, step_score, is_final,
        )

        return {
            "session_id": str(session.id),
            "step_number": next_step_number,
            "step_score": step_score,
            "running_total_score": round(session.total_score, 2),
            "feedback": feedback_text,
            "next_scenario": next_scenario,
            "is_final": is_final,
            "error_flags": error_flags,
            "strengths": strengths,
            "session_status": session.status,
            "coins_earned": None,  # Populated after close
        }

    @staticmethod
    @transaction.atomic
    def _close_session(session) -> None:
        """
        Transitions session to COMPLETED or FAILED.
        Awards coins if COMPLETED (handled by BillingService).
        Decrements active session count.
        """
        from apps.simulation.models import SimulationSession

        final_score = session.total_score
        if final_score >= session.case.passing_score:
            session.status = SimulationSession.Status.COMPLETED
        else:
            session.status = SimulationSession.Status.FAILED

        session.completed_at = timezone.now()
        session.save(update_fields=[
            "status", "completed_at", "steps_taken", "total_score",
            "current_step", "error_analysis", "last_activity_at"
        ])

        # Decrement active sessions count
        UserQuotaUsage.objects.filter(user=session.student).update(
            active_sessions_count=F("active_sessions_count") - 1
        )

        # Reward if completed
        if session.status == SimulationSession.Status.COMPLETED:
            try:
                BillingService.reward_user_for_completion(session.student, session)
            except Exception as exc:
                logger.exception("Failed to reward user %s: %s", session.student.email, exc)

        # Update streak
        SimulationEngineService._update_streak(session.student)

        logger.info(
            "Session closed: %s status=%s score=%.1f",
            session.id, session.status, session.total_score,
        )

    @staticmethod
    @transaction.atomic
    def abandon_session(session_id: str, student) -> None:
        """Marks a session as ABANDONED and frees the quota slot."""
        from apps.simulation.models import SimulationSession

        session = SimulationSession.objects.select_for_update().get(
            id=session_id, student=student, status=SimulationSession.Status.ACTIVE
        )
        session.status = SimulationSession.Status.ABANDONED
        session.completed_at = timezone.now()
        session.save(update_fields=["status", "completed_at"])

        UserQuotaUsage.objects.filter(user=student).update(
            active_sessions_count=F("active_sessions_count") - 1
        )
        logger.info("Session abandoned: %s by %s", session_id, student.email)

    # ── AI Call ───────────────────────────────────────────────────────────────

    @staticmethod
    def _call_ai(
        session,
        student_input: str,
        rag_context: str,
        conversation_history: str,
        force_final: bool = False,
    ) -> Tuple[Dict[str, Any], int, int]:
        """
        Calls OpenAI ChatCompletion with the structured prompt.
        Returns (parsed_response_dict, prompt_tokens, completion_tokens).
        Falls back to a mock response in development (no API key).
        """
        import json

        rubric_str = json.dumps(session.case.grading_rubric, indent=2) if session.case.grading_rubric else "{}"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            domain=session.case.course.domain.name,
            role_context=session.case.role_context,
            rag_context=rag_context,
            case_description=session.case.description,
            rubric=rubric_str,
            schema=json.dumps(AI_RESPONSE_SCHEMA, indent=2),
            conversation_history=conversation_history or "None yet.",
            student_input=student_input,
        )

        if force_final:
            system_prompt += "\n\nIMPORTANT: This is the FINAL step. Set is_final=true in your response."

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Returning mock AI response.")
            return SimulationEngineService._mock_ai_response(student_input, force_final), 0, 0

        try:
            import openai
            client = openai.OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model=settings.AI_CHAT_MODEL,
                temperature=settings.AI_TEMPERATURE,
                max_tokens=settings.AI_MAX_TOKENS,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": student_input},
                ],
            )

            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

            return parsed, prompt_tokens, completion_tokens

        except json.JSONDecodeError as e:
            logger.error("AI returned invalid JSON: %s", e)
            raise AIResponseParseError(f"AI returned invalid JSON: {e}")
        except Exception as exc:
            logger.exception("AI API call failed: %s", exc)
            raise

    @staticmethod
    def _mock_ai_response(student_input: str, is_final: bool = False) -> Dict[str, Any]:
        """Development mock when OpenAI API key is absent."""
        return {
            "feedback": (
                f"[DEV MODE] Your response '{student_input[:50]}...' has been received. "
                "In production, this will be evaluated by GPT-4o against the knowledge base."
            ),
            "step_score": 75.0,
            "next_scenario": "" if is_final else "Please proceed to the next step of the analysis.",
            "is_final": is_final,
            "error_flags": [],
            "strengths": ["Engagement with the material"],
            "knowledge_gap": "",
        }

    # ── Streak Management ─────────────────────────────────────────────────────

    @staticmethod
    def _update_streak(student) -> None:
        """Updates daily streak and awards streak bonuses."""
        from django.utils.timezone import now
        profile = student.profile
        today = now().date()

        if profile.last_activity_date == today:
            return  # Already counted today

        if profile.last_activity_date and (today - profile.last_activity_date).days == 1:
            profile.current_streak_days += 1
        else:
            profile.current_streak_days = 1

        if profile.current_streak_days > profile.longest_streak_days:
            profile.longest_streak_days = profile.current_streak_days

        profile.last_activity_date = today
        profile.save(update_fields=["current_streak_days", "longest_streak_days", "last_activity_date"])

        # Award streak bonus (7, 14, 30, 60, 100 days)
        try:
            BillingService.award_streak_bonus(student, profile.current_streak_days)
        except Exception:
            pass



