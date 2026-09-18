import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { simulationApi } from '../services/api';
import AppleSticker from '../components/AppleSticker';

export default function SimulationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();

  // State: Case Selection & Active Session
  const [cases, setCases] = useState([]);
  const [loadingCases, setLoadingCases] = useState(true);
  const [selectedCase, setSelectedCase] = useState(null);
  const [session, setSession] = useState(null); // Active session metadata
  const [history, setHistory] = useState([]); // List of turns/steps taken
  const [studentInput, setStudentInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [completedSession, setCompletedSession] = useState(null);

  const turnsEndRef = useRef(null);

  // Auto-scroll to latest turn
  useEffect(() => {
    turnsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, isSubmitting]);

  // Load available simulation cases
  useEffect(() => {
    async function loadCases() {
      setLoadingCases(true);
      try {
        const res = await simulationApi.getScenarios();
        const data = res.data;
        const list = Array.isArray(data) ? data : data?.results || [];
        setCases(list);

        // Check if query param ?caseId=... was passed
        const preselectedId = searchParams.get('caseId');
        if (preselectedId) {
          const found = list.find((c) => c.id === preselectedId);
          if (found) setSelectedCase(found);
        }
      } catch (err) {
        console.error('Failed to load simulation cases:', err);
        setErrorMessage("Simulyatsiyalarni yuklashda xatolik yuz berdi.");
      } finally {
        setLoadingCases(false);
      }
    }
    loadCases();
  }, [searchParams]);

  // Start a new simulation session
  async function handleStartSession(caseObj) {
    setSelectedCase(caseObj);
    setErrorMessage('');
    setIsSubmitting(true);
    try {
      const res = await simulationApi.createSession(caseObj.id);
      const sessionData = res.data?.data || res.data;
      setSession(sessionData);
      if (Array.isArray(sessionData.step_logs) && sessionData.step_logs.length > 0) {
        setHistory(sessionData.step_logs);
      } else {
        setHistory([]);
      }
      setCompletedSession(null);
    } catch (err) {
      console.error('Start session failed:', err);
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        (typeof err.response?.data === 'string' ? err.response?.data : null) ||
        "Simulyatsiyani boshlashda xatolik yuz berdi.";
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Submit student turn to AI
  async function handleSendTurn(e) {
    e?.preventDefault();
    if (!studentInput.trim() || isSubmitting || !session) return;

    const currentText = studentInput.trim();
    setStudentInput('');
    setIsSubmitting(true);
    setErrorMessage('');

    // Optimistically add student's message
    const tempStepNumber = history.length + 1;
    const pendingStep = {
      step_number: tempStepNumber,
      student_input: currentText,
      loading: true,
    };
    setHistory((prev) => [...prev, pendingStep]);

    try {
      const res = await simulationApi.sendTurn(session.session_id || session.id, currentText);
      const data = res.data?.data || res.data;

      // Update the step with AI evaluation
      setHistory((prev) =>
        prev.map((item, idx) => (idx === prev.length - 1 ? { ...data, student_input: currentText, loading: false } : item))
      );

      // Check if session finished
      if (data.is_final) {
        setCompletedSession({
          ...session,
          final_score: data.running_total_score || data.step_score,
          is_passed: (data.running_total_score || data.step_score) >= (session.passing_score || 70),
          coins_earned: data.coins_earned || session.coin_reward || 25,
        });
      }
    } catch (err) {
      console.error('Submit turn failed:', err);
      const msg = err.response?.data?.error?.message || "AI tahlil qilishda xatolik yuz berdi. Qayta urinib ko'ring.";
      setErrorMessage(msg);
      // Remove loading step on failure
      setHistory((prev) => prev.slice(0, -1));
      setStudentInput(currentText);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Abandon active session
  async function handleAbandonSession() {
    if (!window.confirm("Rostdan ham ushbu simulyatsiyani to'xtatmoqchimisiz?")) return;
    if (session) {
      try {
        await simulationApi.abandonSession(session.session_id || session.id);
      } catch (err) {
        console.error('Abandon session error:', err);
      }
    }
    setSession(null);
    setHistory([]);
    setSelectedCase(null);
    setCompletedSession(null);
  }

  const latestTurn = history[history.length - 1];
  const currentRunningScore = latestTurn?.running_total_score ?? null;

  return (
    <div className="min-h-screen bg-[#0F172A] text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="h-16 border-b border-slate-800 bg-[#0B1120]/80 backdrop-blur-md sticky top-0 z-30 px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-all"
          >
            ← Boshqaruv paneli
          </Link>
          <div className="h-4 w-px bg-slate-700 hidden sm:block" />
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
              <AppleSticker symbol="🤖" size={18} />
            </div>
            <span className="font-display font-bold text-slate-100 text-[16px]">
              OmniLab AI <span className="text-blue-400 font-normal text-xs ml-1 px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20">Gemini 2.5 Flash</span>
            </span>
          </div>
        </div>

        {/* Status / User Info */}
        <div className="flex items-center gap-4">
          {session && !completedSession && (
            <button
              onClick={handleAbandonSession}
              className="text-xs text-rose-400 hover:text-rose-300 px-3 py-1.5 rounded-lg border border-rose-500/20 hover:bg-rose-500/10 transition-all font-medium"
            >
              Chiqish
            </button>
          )}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300">
            <AppleSticker symbol="🏆" size={16} />
            <span className="font-semibold text-amber-400">{user?.profile?.total_coins_earned ?? 0} tanga</span>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col">
        {/* Error notification */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-rose-950/50 border border-rose-800/60 text-rose-200 text-sm flex items-center justify-between animate-fadeIn">
            <div className="flex items-center gap-2">
              <span className="text-rose-400 font-bold">⚠️ Xatolik:</span>
              <span>{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage('')} className="text-rose-400 hover:text-rose-200 text-xs font-semibold">
              Yopish
            </button>
          </div>
        )}

        {/* CASE 1: Session Completed Screen */}
        {completedSession ? (
          <div className="flex-1 flex items-center justify-center py-8">
            <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-3xl p-8 shadow-2xl text-center flex flex-col items-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/30 mb-6">
                <AppleSticker symbol={completedSession.is_passed ? "🏆" : "🎯"} size={40} />
              </div>
              <h2 className="text-2xl font-bold font-display text-white mb-2">
                {completedSession.is_passed ? "Simulyatsiya Muvaffaqiyatli Yakunlandi!" : "Simulyatsiya Tugadi"}
              </h2>
              <p className="text-slate-400 text-sm mb-6">
                {completedSession.is_passed
                  ? "Siz vaziyatni muvaffaqiyatli tahlil qildingiz va sinovdan o'tdingiz!"
                  : "O'tish baliga biroz yetmadi. Qayta urinib ko'rishingiz mumkin."}
              </p>

              {/* Score card */}
              <div className="w-full bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 mb-6">
                <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">Yakuniy Ball</div>
                <div className="text-4xl font-extrabold text-blue-400 font-display">
                  {Math.round(completedSession.final_score)}%
                </div>
                <div className="mt-2 text-xs text-slate-400">
                  O'tish talabi: <span className="font-semibold text-slate-300">{completedSession.passing_score || 70}%</span>
                </div>
                {completedSession.is_passed && (
                  <div className="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-center gap-2 text-amber-400 font-bold text-sm">
                    <AppleSticker symbol="✨" size={18} />
                    <span>+{completedSession.coins_earned} Tanga hisobingizga o'tkazildi!</span>
                  </div>
                )}
              </div>

              <div className="flex gap-3 w-full">
                <button
                  onClick={() => {
                    setSession(null);
                    setCompletedSession(null);
                    setHistory([]);
                  }}
                  className="flex-1 py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm transition-all"
                >
                  Boshqa Case
                </button>
                <Link
                  to="/dashboard"
                  className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm transition-all flex items-center justify-center"
                >
                  Boshqaruv Paneli
                </Link>
              </div>
            </div>
          </div>
        ) : !session ? (
          /* CASE 2: Select a Simulation Case */
          <div className="flex-1 flex flex-col">
            <div className="mb-8 text-center max-w-2xl mx-auto">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold mb-3">
                <AppleSticker symbol="⚡" size={14} />
                <span>Interaktiv AI Laboratoriyasi</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold font-display text-white tracking-tight">
                Haqiqiy Vaziyatlar Simulyatsiyasi
              </h1>
              <p className="text-slate-400 text-sm mt-2">
                Gemini 2.5 Flash va RAG bilimlar bazasi orqali real keyslarni tahlil qiling, sun'iy intellekt tomonidan har bir qadamingiz baholanadi.
              </p>
            </div>

            {loadingCases ? (
              <div className="grid md:grid-cols-2 gap-6">
                {[1, 2].map((i) => (
                  <div key={i} className="h-64 rounded-3xl bg-slate-800/40 border border-slate-800 animate-pulse" />
                ))}
              </div>
            ) : cases.length === 0 ? (
              <div className="text-center py-16 bg-slate-900/40 border border-slate-800 rounded-3xl p-8">
                <AppleSticker symbol="📚" size={48} className="mx-auto mb-4" />
                <h3 className="text-lg font-bold text-slate-200">Hozircha faol keyslar mavjud emas</h3>
                <p className="text-slate-400 text-sm mt-1">Admin yoki o'qituvchi keys qo'shganda bu yerda ko'rinadi.</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 gap-6">
                {cases.map((c) => {
                  const isTech = c.slug?.includes('sqli') || c.title?.toLowerCase().includes('sql') || c.title?.toLowerCase().includes('kiber');
                  return (
                    <div
                      key={c.id}
                      className="bg-gradient-to-b from-slate-900/90 to-slate-900/50 border border-slate-800 hover:border-blue-500/50 rounded-3xl p-6 sm:p-7 flex flex-col justify-between transition-all duration-300 hover:shadow-2xl hover:shadow-blue-500/10 group"
                    >
                      <div>
                        {/* Top tags */}
                        <div className="flex items-center justify-between gap-2 mb-4">
                          <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                            c.difficulty === 'EASY'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : c.difficulty === 'HARD'
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}>
                            {c.difficulty || 'MEDIUM'}
                          </span>
                          <div className="flex items-center gap-1.5 text-xs text-amber-400 font-bold bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full">
                            <AppleSticker symbol="🏆" size={14} />
                            <span>+{c.coin_reward || 25} tanga</span>
                          </div>
                        </div>

                        {/* Title & Icon */}
                        <div className="flex items-start gap-4 mb-3">
                          <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${
                            isTech ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                          }`}>
                            <AppleSticker symbol={isTech ? "🛡️" : "⚖️"} size={26} />
                          </div>
                          <div>
                            <h3 className="font-display font-bold text-lg text-white group-hover:text-blue-400 transition-colors">
                              {c.title}
                            </h3>
                            <p className="text-xs text-slate-400 mt-0.5">
                              Rol: <span className="text-slate-300 font-medium">{c.role_context}</span>
                            </p>
                          </div>
                        </div>

                        <p className="text-slate-300 text-sm leading-relaxed mb-6 line-clamp-3">
                          {c.description}
                        </p>
                      </div>

                      {/* Footer Specs & Launch button */}
                      <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
                        <div className="flex items-center gap-4 text-xs text-slate-400">
                          <div>
                            Qadamlar: <span className="text-slate-200 font-semibold">{c.max_steps || 4} ta</span>
                          </div>
                          <div>
                            O'tish bali: <span className="text-slate-200 font-semibold">{c.passing_score || 70}%</span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleStartSession(c)}
                          disabled={isSubmitting}
                          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all shadow-lg shadow-blue-600/30 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
                        >
                          {isSubmitting && selectedCase?.id === c.id ? "Boshlanmoqda..." : "Simulyatsiyani Boshlash →"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          /* CASE 3: Interactive Simulation Room */
          <div className="flex-1 grid lg:grid-cols-3 gap-6">
            {/* Left: Chat & Step Evaluation History (2 Columns) */}
            <div className="lg:col-span-2 flex flex-col bg-slate-900/80 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
              {/* Simulation Banner */}
              <div className="p-5 bg-gradient-to-r from-slate-900 via-blue-950/40 to-slate-900 border-b border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                    Jonli Simulyatsiya Sessiyasi
                  </span>
                  <span className="text-xs text-slate-400 font-medium">
                    Qadam: {history.length} / {session.max_steps || 4}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white font-display">{session.case_title || selectedCase?.title}</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Sizning vazifangiz: <span className="text-blue-300 font-semibold">{session.role_context}</span>
                </p>
              </div>

              {/* Turns Stream */}
              <div className="flex-1 p-5 overflow-y-auto space-y-6 max-h-[580px]">
                {/* Initial Case Briefing Card */}
                <div className="p-5 rounded-2xl bg-blue-950/20 border border-blue-900/40 text-slate-300 text-sm">
                  <div className="flex items-center gap-2 font-bold text-blue-400 text-xs uppercase tracking-wider mb-2">
                    <AppleSticker symbol="📋" size={14} />
                    <span>Dastlabki Vaziyat Tavsifi</span>
                  </div>
                  <p className="leading-relaxed whitespace-pre-wrap">{session.description}</p>
                </div>

                {/* Turns loop */}
                {history.map((step, idx) => (
                  <div key={idx} className="space-y-4 animate-fadeIn">
                    {/* Student Turn */}
                    <div className="flex justify-end">
                      <div className="max-w-[85%] bg-blue-600/90 text-white p-4 rounded-2xl rounded-br-sm shadow-md text-sm">
                        <div className="text-[11px] text-blue-200 font-semibold mb-1">
                          Sizning javobingiz (Qadam #{step.step_number || idx + 1})
                        </div>
                        <p className="whitespace-pre-wrap leading-relaxed">{step.student_input}</p>
                      </div>
                    </div>

                    {/* AI Evaluation Turn */}
                    {step.loading ? (
                      <div className="flex justify-start">
                        <div className="bg-slate-800/80 border border-slate-700/60 p-4 rounded-2xl rounded-bl-sm flex items-center gap-3 text-slate-300 text-sm">
                          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                          <span>Gemini AI tahlil qilmoqda va RAG bilimlar bazasini tekshirmoqda...</span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex justify-start">
                        <div className="max-w-[95%] w-full bg-slate-800/60 border border-slate-700/60 p-5 rounded-2xl rounded-bl-sm shadow-lg space-y-4">
                          {/* AI Header & Score badge */}
                          <div className="flex items-center justify-between border-b border-slate-700/40 pb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                <AppleSticker symbol="🤖" size={14} />
                              </div>
                              <span className="text-xs font-bold text-slate-200">AI Mutaxassis Bahosi</span>
                            </div>
                            <div className={`px-3 py-1 rounded-full text-xs font-extrabold ${
                              step.step_score >= 70
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                            }`}>
                              Baho: {step.step_score}/100
                            </div>
                          </div>

                          {/* Feedback text */}
                          <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">{step.feedback}</p>

                          {/* Strengths & Errors */}
                          {(step.strengths?.length > 0 || step.error_flags?.length > 0) && (
                            <div className="grid sm:grid-cols-2 gap-3 pt-2">
                              {step.strengths?.length > 0 && (
                                <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/30">
                                  <div className="text-[11px] font-bold text-emerald-400 mb-1.5 flex items-center gap-1">
                                    <AppleSticker symbol="✨" size={12} />
                                    <span>Kuchli tomonlar:</span>
                                  </div>
                                  <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                                    {step.strengths.map((s, i) => (
                                      <li key={i}>{s}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {step.error_flags?.length > 0 && (
                                <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-800/30">
                                  <div className="text-[11px] font-bold text-rose-400 mb-1.5 flex items-center gap-1">
                                    <AppleSticker symbol="⚠️" size={12} />
                                    <span>E'tibor qaratish kerak:</span>
                                  </div>
                                  <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                                    {step.error_flags.map((e, i) => (
                                      <li key={i}>{e}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Next Scenario Prompt */}
                          {step.next_scenario && !step.is_final && (
                            <div className="p-3.5 rounded-xl bg-blue-900/20 border border-blue-800/40 text-blue-200 text-xs leading-relaxed">
                              <span className="font-bold text-blue-400 uppercase tracking-wider block mb-1">
                                Keyingi vaziyat / Savol:
                              </span>
                              {step.next_scenario}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={turnsEndRef} />
              </div>

              {/* Input Form */}
              <form onSubmit={handleSendTurn} className="p-4 bg-slate-950 border-t border-slate-800 flex flex-col gap-2">
                <div className="relative">
                  <textarea
                    rows={3}
                    value={studentInput}
                    onChange={(e) => setStudentInput(e.target.value)}
                    placeholder="Vaziyatni tahlil qiling, o'z qaroringiz yoki javobingizni asoslab yozing..."
                    disabled={isSubmitting || latestTurn?.is_final}
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-2xl p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all resize-none disabled:opacity-50"
                  />
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-[11px] text-slate-500">
                      Shift+Enter yangi qator, Enter yuborish
                    </span>
                    <button
                      type="submit"
                      disabled={isSubmitting || !studentInput.trim() || latestTurn?.is_final}
                      className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold shadow-lg shadow-blue-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {isSubmitting ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>AI Baholamoqda...</span>
                        </>
                      ) : (
                        <>
                          <span>Yuborish</span>
                          <AppleSticker symbol="🚀" size={14} />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            </div>

            {/* Right: Live Metrics & Knowledge Grounding Sidebar (1 Column) */}
            <div className="flex flex-col gap-6">
              {/* Score card */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl flex flex-col items-center text-center">
                <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-2">Joriy O'rtacha Ball</div>
                <div className="relative flex items-center justify-center mb-4">
                  <div className="w-32 h-32 rounded-full border-4 border-slate-800 flex items-center justify-center bg-slate-950/60">
                    <span className="text-3xl font-black font-display text-blue-400">
                      {currentRunningScore !== null ? `${Math.round(currentRunningScore)}%` : '—'}
                    </span>
                  </div>
                </div>

                <div className="w-full grid grid-cols-2 gap-3 pt-4 border-t border-slate-800/80 text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-800/40">
                    <div className="text-slate-400">O'tish talabi</div>
                    <div className="font-bold text-slate-200 mt-0.5">{session.passing_score || 70}%</div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-800/40">
                    <div className="text-slate-400">Mukofot</div>
                    <div className="font-bold text-amber-400 mt-0.5">+{session.coin_reward || 25} tanga</div>
                  </div>
                </div>
              </div>

              {/* RAG Grounding Info Card */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl text-xs space-y-4">
                <div className="flex items-center gap-2 font-bold text-slate-200">
                  <AppleSticker symbol="💡" size={18} />
                  <span>AI Baholash Qoidalari</span>
                </div>
                <p className="text-slate-400 leading-relaxed">
                  Ushbu simulyatsiya darslikning rasmiy bilimlar bazasi (RAG) asosida tekshiriladi. Zero-hallucination tizimi sizning javobingizni qonuniy me'yorlar va standartlar bilan solishtiradi.
                </p>
                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 space-y-1.5">
                  <div className="font-semibold text-blue-200">Tavsiyalar:</div>
                  <div>• Aniq atamalar va formulalardan foydalaning.</div>
                  <div>• Har bir qaroringizni mantiqiy asoslab bering.</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
