import './index.css';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import HowItWorks from './components/HowItWorks';
import Features from './components/Features';
import Testimonials from './components/Testimonials';
import Pricing from './components/Pricing';
import Footer from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-white text-[#161C2D]" style={{ fontFamily: "'Inter', sans-serif" }}>
      <Navbar />

      <main>
        <Hero />
        <HowItWorks />
        <Features />
        <Testimonials />
        <Pricing />
      </main>

      <Footer />
    </div>
  );
}
