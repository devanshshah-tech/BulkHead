import React from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';

const pillars = [
  { to: '/docs/tutorials', emoji: '🎓', title: 'Tutorials', text: 'Zero to grounded answers in one sitting.' },
  { to: '/docs/how-to', emoji: '🧭', title: 'How-to guides', text: 'Recipes: rotate IPs, swap models, operate.' },
  { to: '/docs/reference', emoji: '📖', title: 'Reference', text: 'APIs, mise tasks, bundle contents, CI.' },
  { to: '/docs/explanation', emoji: '💡', title: 'Explanation', text: 'Architecture and design decisions.' },
];

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout description={siteConfig.tagline}>
      <main style={{ maxWidth: 960, margin: '0 auto', padding: '3rem 1rem' }}>
        <h1>{siteConfig.title}</h1>
        <p style={{ fontSize: '1.25rem' }}>{siteConfig.tagline}</p>
        <p>
          A production-style Retrieval-Augmented Generation platform designed to run{' '}
          <strong>fully disconnected</strong>. Ships as a single Zarf airgap bundle, deployed via
          ArgoCD GitOps, with mTLS-secured service mesh (Istio), reproducible dev tooling (mise),
          and versioned document corpora (lakeFS). Includes a live connected-mode demo and a
          downloadable airgap bundle you can run yourself.
        </p>
        <p>
          <Link className="button button--primary button--lg" to="/docs/tutorials/quickstart">
            Quickstart — 5 min
          </Link>{' '}
          <Link
            className="button button--secondary button--lg"
            href="https://github.com/devanshshah-tech/BulkHead/releases/latest"
          >
            Download airgap bundle
          </Link>
        </p>
        <h2>Read the docs</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '1rem' }}>
          {pillars.map((p) => (
            <Link key={p.to} to={p.to} style={{ border: '1px solid var(--ifm-color-emphasis-300)', borderRadius: 12, padding: '1rem', textDecoration: 'none' }}>
              <div style={{ fontSize: '1.6rem' }}>{p.emoji}</div>
              <h3 style={{ color: 'inherit' }}>{p.title}</h3>
              <p style={{ color: 'var(--ifm-color-emphasis-700)' }}>{p.text}</p>
            </Link>
          ))}
        </div>
      </main>
    </Layout>
  );
}
