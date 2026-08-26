import React from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

const pillars = [
  { to: '/docs/tutorials', emoji: '🎓', title: 'Tutorials', text: 'Learning-oriented lessons — zero to grounded answers.' },
  { to: '/docs/how-to', emoji: '🧭', title: 'How-to guides', text: 'Goal-oriented recipes for specific tasks.' },
  { to: '/docs/reference', emoji: '📖', title: 'Reference', text: 'Technical descriptions: APIs, tasks, bundle contents.' },
  { to: '/docs/explanation', emoji: '💡', title: 'Explanation', text: 'Architecture and design decisions.' },
];

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <main style={{ maxWidth: 960, margin: '0 auto', padding: '3rem 1rem' }}>
      <h1>{siteConfig.title}</h1>
      <p style={{ fontSize: '1.25rem' }}>{siteConfig.tagline}</p>
      <p>
        A production-style Retrieval-Augmented Generation platform that runs fully disconnected:
        shipped as a single Zarf/UDS airgap bundle, operated through GitOps, secured with an Istio
        mTLS mesh, with corpora versioned in lakeFS.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '1rem', marginTop: '2rem' }}>
        {pillars.map((p) => (
          <Link key={p.to} to={p.to} style={{ border: '1px solid #e3e6ea', borderRadius: 12, padding: '1rem', textDecoration: 'none' }}>
            <div style={{ fontSize: '1.6rem' }}>{p.emoji}</div>
            <h3 style={{ color: 'inherit' }}>{p.title}</h3>
            <p style={{ color: '#65727f' }}>{p.text}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
