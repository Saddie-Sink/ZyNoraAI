import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../../context/ProjectContext';
import StepIndicator from '../common/StepIndicator';
import ProgressBar from '../common/ProgressBar';
import Button from '../common/Button';

import Step1Project from './steps/Step1Project';
import Step2Location from './steps/Step2Location';
import Step3Property from './steps/Step3Property';
import Step4Family from './steps/Step4Family';
import Step5Budget from './steps/Step5Budget';
import Step6Style from './steps/Step6Style';
import Step7FloorPlan from './steps/Step7FloorPlan';
import Step8Review from './steps/Step8Review';

const STEP_TITLES = {
  1: { badge: 'Step 01 / 08', title: 'Project Foundations', desc: 'Define project identity, construction typology, and fundamental purpose.' },
  2: { badge: 'Step 02 / 08', title: 'Site Location & Orientation', desc: 'Specify geographical placement and road-facing solar orientation.' },
  3: { badge: 'Step 03 / 08', title: 'Property & Parcel Boundaries', desc: 'Input parcel width, length, floor count, and target built-up footprint.' },
  4: { badge: 'Step 04 / 08', title: 'Household Program & Rooms', desc: 'Detail family composition, bedroom count, and accessibility priorities.' },
  5: { badge: 'Step 05 / 08', title: 'Budget & Material Priorities', desc: 'Establish construction budget limits and quality tier allocations.' },
  6: { badge: 'Step 06 / 08', title: 'Architectural Style & Materials', desc: 'Select design aesthetics, exterior material palette, and custom details.' },
  7: { badge: 'Step 07 / 08', title: 'Floor Plan Strategy', desc: 'Choose between AI requirements generation or blueprint CAD upload.' },
  8: { badge: 'Step 08 / 08', title: 'Review & Synthesize', desc: 'Verify all project parameters before launching candidate generation.' }
};

export default function WizardShell() {
  const navigate = useNavigate();
  const { project, activeStep, setActiveStep } = useProject();

  const handleNext = () => {
    if (activeStep < 8) {
      setActiveStep(activeStep + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePrev = () => {
    if (activeStep > 1) {
      setActiveStep(activeStep - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const currentMeta = STEP_TITLES[activeStep] || STEP_TITLES[1];
  const progressPercent = (activeStep / 8) * 100;

  return (
    <div className="wizard">
      {/* Left Wizard Sidebar */}
      <aside className="wizard__sidebar" aria-label="Wizard Steps">
        <div className="wizard__sidebar-header">
          <div className="wizard__sidebar-title">Project Setup</div>
          <div className="wizard__sidebar-project" title={project.name || 'Untitled Home'}>
            {project.name || 'Villa Aurelia'}
          </div>
        </div>

        <StepIndicator activeStep={activeStep} onSelectStep={setActiveStep} />

        <div style={{ marginTop: 'auto', paddingTop: '2rem' }}>
          <ProgressBar progress={progressPercent} showLabel={true} />
        </div>
      </aside>

      {/* Main Wizard Form Body */}
      <main className="wizard__main" role="main">
        <div className="wizard__step-header">
          <span className="wizard__step-badge">{currentMeta.badge}</span>
          <h2 className="wizard__step-title">{currentMeta.title}</h2>
          <p className="wizard__step-desc">{currentMeta.desc}</p>
        </div>

        {activeStep === 1 && <Step1Project />}
        {activeStep === 2 && <Step2Location />}
        {activeStep === 3 && <Step3Property />}
        {activeStep === 4 && <Step4Family />}
        {activeStep === 5 && <Step5Budget />}
        {activeStep === 6 && <Step6Style />}
        {activeStep === 7 && <Step7FloorPlan />}
        {activeStep === 8 && <Step8Review onEditStep={(stepNum) => setActiveStep(stepNum)} />}

        <div className="wizard__footer">
          <div>
            {activeStep > 1 && (
              <Button variant="outline" onClick={handlePrev}>
                ← Previous
              </Button>
            )}
          </div>

          <div className="wizard__footer-right">
            {activeStep < 8 && (
              <Button variant="primary" onClick={handleNext}>
                Continue to Step {activeStep + 1} →
              </Button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
