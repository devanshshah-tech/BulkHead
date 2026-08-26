// @ts-check
const lightCodeTheme = require('prism-react-renderer').themes.github;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Bulkhead',
  tagline: 'An airgap-deployable RAG platform',
  url: 'https://demo.bulkhead.cc',
  baseUrl: '/',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  organizationName: 'devanshshah-tech',
  projectName: 'BulkHead',
  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          // Diátaxis pillars live at the repo root: docs/{tutorials,how-to,reference,explanation}
          path: '../docs',
          routeBasePath: 'docs',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/devanshshah-tech/BulkHead/edit/main/',
        },
        blog: false,
      }),
    ],
  ],
  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'Bulkhead',
        items: [
          { to: '/docs/tutorials/quickstart', label: 'Quickstart', position: 'left' },
          {
            type: 'dropdown',
            label: 'Diátaxis',
            position: 'left',
            items: [
              { to: '/docs/tutorials', label: 'Tutorials' },
              { to: '/docs/how-to', label: 'How-to guides' },
              { to: '/docs/reference', label: 'Reference' },
              { to: '/docs/explanation', label: 'Explanation' },
            ],
          },
          {
            href: 'https://github.com/devanshshah-tech/BulkHead',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        copyright: `Bulkhead — built to run where the internet isn't.`,
      },
    }),
};

module.exports = config;
