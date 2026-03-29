import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    'quarter-overview',
    'why-physical-ai-matters',
    'learning-outcomes', // Added
    {
      type: 'category',
      label: 'Modules',
      items: [
        // Placeholder for future modules (ROS 2, Gazebo & Unity, NVIDIA Isaac, Vision-Language-Action)
        // For now, these are part of the 'quarter-overview' text, not separate docs.
      ],
    },
    {
      type: 'category',
      label: 'Weekly Breakdown',
      items: [
        'weekly-breakdown', // Point to the main weekly breakdown document
      ],
    },
    'assessments',
    'hardware-requirements',
  ],
};

export default sidebars;