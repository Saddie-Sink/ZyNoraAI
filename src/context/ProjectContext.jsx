import React, { createContext, useContext, useState, useEffect } from 'react';
import { INITIAL_PROJECT_STATE, DEMO_CANDIDATES } from '../data/demoData';

const ProjectContext = createContext(null);

const STORAGE_KEY = 'zynora_ml_project_state_v2';
const PROJECTS_LIST_KEY = 'zynora_user_projects_v3';

export function ProjectProvider({ children }) {
  const [project, setProject] = useState(() => {
    try {
      const cached = localStorage.getItem(STORAGE_KEY);
      if (cached) return JSON.parse(cached);
    } catch (e) {
      console.warn('Could not read project from localStorage', e);
    }
    return INITIAL_PROJECT_STATE;
  });

  const [projectsList, setProjectsList] = useState(() => {
    try {
      const cached = localStorage.getItem(PROJECTS_LIST_KEY);
      if (cached) return JSON.parse(cached);
    } catch (e) {
      console.warn('Could not read projects list from localStorage', e);
    }
    return [];
  });

  const [activeStep, setActiveStep] = useState(1);
  const [candidatesList, setCandidatesList] = useState(DEMO_CANDIDATES);
  const [selectedCandidateId, setSelectedCandidateId] = useState('cand-b');

  const setCandidates = (newCandidates) => {
    if (Array.isArray(newCandidates) && newCandidates.length > 0) {
      setCandidatesList(newCandidates);
      const topRank = newCandidates.find(c => c.isTopRank) || newCandidates[0];
      if (topRank) {
        setSelectedCandidateId(topRank.id);
      }
    }
  };

  const selectedCandidate = candidatesList.find(c => c.id === selectedCandidateId) || candidatesList[0] || DEMO_CANDIDATES[0];

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(project));
    } catch (e) {
      // ignore storage quota
    }
  }, [project]);

  useEffect(() => {
    try {
      localStorage.setItem(PROJECTS_LIST_KEY, JSON.stringify(projectsList));
    } catch (e) {
      // ignore
    }
  }, [projectsList]);

  const updateProject = (fieldOrObject, value) => {
    setProject((prev) => {
      if (typeof fieldOrObject === 'string') {
        return {
          ...prev,
          [fieldOrObject]: typeof value === 'object' && !Array.isArray(value)
            ? { ...prev[fieldOrObject], ...value }
            : value
        };
      }
      return { ...prev, ...fieldOrObject };
    });
  };

  const updateNested = (category, subfield, value) => {
    setProject((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [subfield]: value
      }
    }));
  };

  const updateRoomCount = (roomName, count) => {
    setProject((prev) => ({
      ...prev,
      family: {
        ...prev.family,
        rooms: {
          ...prev.family.rooms,
          [roomName]: Math.max(0, count)
        }
      }
    }));
  };

  const toggleRequirement = (reqName) => {
    setProject((prev) => {
      const current = prev.family.requirements || [];
      const updated = current.includes(reqName)
        ? current.filter(r => r !== reqName)
        : [...current, reqName];
      return {
        ...prev,
        family: {
          ...prev.family,
          requirements: updated
        }
      };
    });
  };

  const toggleMaterial = (matName) => {
    setProject((prev) => {
      const current = prev.style.materialPreferences || [];
      const updated = current.includes(matName)
        ? current.filter(m => m !== matName)
        : [...current, matName];
      return {
        ...prev,
        style: {
          ...prev.style,
          materialPreferences: updated
        }
      };
    });
  };

  const selectCandidate = (id) => {
    setSelectedCandidateId(id);
    setProject(prev => ({ ...prev, selectedCandidateId: id }));
  };

  const saveProjectToDashboard = () => {
    const locCity = project.location?.city || 'Local Site';
    const locState = project.location?.state ? `, ${project.location.state}` : '';
    const builtArea = project.property?.builtUpArea || 2400;
    const siteW = project.property?.siteWidth || 30;
    const siteD = project.property?.siteLength || 40;
    const floors = project.property?.floors || 2;
    const beds = project.family?.rooms?.bedrooms || 3;
    const baths = project.family?.rooms?.bathrooms || 3;

    const newEntry = {
      id: project.id || 'proj-' + Date.now().toString(36),
      name: project.name || 'My Home Floor Plan',
      type: project.projectType || 'Independent House',
      purpose: project.purpose || 'New Construction',
      city: `${locCity}${locState}`,
      area: `${builtArea} sq ft`,
      floors,
      style: project.style?.architecturalStyle || 'Modern',
      status: 'Ready',
      updatedAt: 'Just now',
      stats: {
        site: `${siteW}′ × ${siteD}′ Plot`,
        rooms: `${beds} BHK · ${baths} Bath`,
        floorsLabel: `${floors} ${floors === 1 ? 'Floor' : 'Floors'}`,
        orientation: `${project.location?.orientation || 'East'} Facing`,
      }
    };

    setProjectsList((prev) => {
      const filtered = prev.filter(p => p.id !== newEntry.id);
      return [newEntry, ...filtered];
    });
  };

  const deleteProject = (projectId) => {
    setProjectsList((prev) => prev.filter(p => p.id !== projectId));
  };

  const resetToDefaultDemo = () => {
    setProject(INITIAL_PROJECT_STATE);
    setSelectedCandidateId('cand-a');
    setActiveStep(1);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {}
  };

  return (
    <ProjectContext.Provider
      value={{
        project,
        projectsList,
        candidatesList,
        setCandidates,
        activeStep,
        setActiveStep,
        selectedCandidateId,
        selectedCandidate,
        updateProject,
        updateNested,
        updateRoomCount,
        toggleRequirement,
        toggleMaterial,
        selectCandidate,
        saveProjectToDashboard,
        deleteProject,
        resetToDefaultDemo
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
