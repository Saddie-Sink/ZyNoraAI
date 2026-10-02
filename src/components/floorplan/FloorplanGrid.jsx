import React from 'react';
import CandidateCard from './CandidateCard';

export default function FloorplanGrid({
  candidates = [],
  selectedId,
  onSelectCandidate
}) {
  return (
    <div className="fp-grid">
      {candidates.map((candidate) => (
        <CandidateCard
          key={candidate.id}
          candidate={candidate}
          isSelected={candidate.id === selectedId}
          onSelect={onSelectCandidate}
        />
      ))}
    </div>
  );
}
