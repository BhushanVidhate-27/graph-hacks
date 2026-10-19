import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { LiveCoordinatesHUD } from './components/LiveCoordinatesHUD';
import { HeroSection } from './components/HeroSection';
import { ViolationInspector } from './components/ViolationInspector';
import { ProblemsSection } from './components/ProblemsSection';
import { ProductShowcaseSection } from './components/ProductShowcaseSection';
import { WorkflowSection } from './components/WorkflowSection';
import { RolesSection } from './components/RolesSection';
import { PricingSection } from './components/PricingSection';
import { FAQSection } from './components/FAQSection';
import { Footer } from './components/Footer';
import { WebsiteViewModule } from './components/WebsiteViewModule';
import { ChatWidgetSimulator } from './components/ChatWidgetSimulator';
import { DashboardSimulator } from './components/DashboardSimulator';
import { DeviceViewportFrame } from './components/DeviceViewportFrame';
import { ViewMode } from './types';

export const App: React.FC = () => {
  const [currentMode, setCurrentMode] = useState<ViewMode>('website');
  const [viewportDevice, setViewportDevice] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');

  const scrollToSection = (sectionId: string) => {
    // If not in website mode, switch first
    if (currentMode !== 'website' && currentMode !== 'viewport') {
      setCurrentMode('website');
      setTimeout(() => {
        const el = document.getElementById(sectionId);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } else {
      const el = document.getElementById(sectionId);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // The full website content
  const renderWebsiteContent = () => (
    <div className="relative w-full">
      <HeroSection 
        onSelectMode={setCurrentMode} 
        onNavigateSection={scrollToSection} 
      />

      <div className="cad-border-t border-[#282828]/15" />
      <ViolationInspector />

      <div className="cad-border-t border-[#282828]/15" />
      <ProblemsSection />

      <div className="cad-border-t border-[#282828]/15" />
      <ProductShowcaseSection onSelectMode={setCurrentMode} />

      <div className="cad-border-t border-[#282828]/15" />
      <WorkflowSection />

      <div className="cad-border-t border-[#282828]/15" />
      <RolesSection />

      <div className="cad-border-t border-[#282828]/15" />
      <PricingSection />

      <div className="cad-border-t border-[#282828]/15" />
      <FAQSection />

      <Footer onSelectMode={setCurrentMode} />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#ecece4] text-[#282828] font-mono relative selection:bg-[#e15c46] selection:text-white pb-20">
      
      {/* Top Fixed Live CAD Coordinates HUD */}
      <LiveCoordinatesHUD />

      {/* Main Navbar */}
      <Navbar 
        currentMode={currentMode} 
        onSelectMode={setCurrentMode} 
        onNavigateSection={scrollToSection} 
      />

      {/* Mode View Content */}
      <main className="w-full">
        {currentMode === 'website' && renderWebsiteContent()}

        {currentMode === 'chat-widget' && (
          <div className="py-8">
            <ChatWidgetSimulator />
          </div>
        )}

        {currentMode === 'dashboard' && (
          <div className="py-8">
            <DashboardSimulator />
          </div>
        )}

        {currentMode === 'viewport' && (
          <DeviceViewportFrame device={viewportDevice}>
            {renderWebsiteContent()}
          </DeviceViewportFrame>
        )}
      </main>

      {/* Interactive Website View Module Bar (User can switch modes / view frames anytime) */}
      <WebsiteViewModule
        currentMode={currentMode}
        onSelectMode={setCurrentMode}
        viewportDevice={viewportDevice}
        onChangeViewportDevice={setViewportDevice}
      />

    </div>
  );
};

export default App;
