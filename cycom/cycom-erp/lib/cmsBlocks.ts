// Shared block-type definitions for the CMS: the public renderer
// (app/site/**) and the page builder (app/cms/**) both key off this so
// `config` keys never drift between "what the builder writes" and "what
// the renderer reads." Kept in sync with the backend's BLOCK_TYPE_CHOICES
// / CONTAINER_BLOCK_TYPES (products/cycom/cms/models.py) — this is a
// frontend-only mirror, not fetched from the API, since it also drives
// the inspector form field list.

export type BlockType =
  | 'section'
  | 'columns'
  | 'heading'
  | 'text'
  | 'image'
  | 'button'
  | 'spacer'
  | 'video'
  | 'html';

export const CONTAINER_BLOCK_TYPES: BlockType[] = ['section', 'columns'];

export interface BlockNode {
  id: string;
  block_type: BlockType;
  order: number;
  config: Record<string, any>;
  children: BlockNode[];
}

export const BLOCK_TYPE_LABELS: Record<BlockType, string> = {
  section: 'Section',
  columns: 'Columns',
  heading: 'Heading',
  text: 'Text',
  image: 'Image',
  button: 'Button',
  spacer: 'Spacer',
  video: 'Video',
  html: 'Custom HTML',
};

export function defaultConfigFor(type: BlockType): Record<string, any> {
  switch (type) {
    case 'section':
      return { background: '#0a0f1e', padding: 48 };
    case 'columns':
      return { column_count: 2 };
    case 'heading':
      return { text: 'Heading', level: 2, align: 'start' };
    case 'text':
      return { text: 'Add your text here.', align: 'start' };
    case 'image':
      return { image_url: '', alt: '' };
    case 'button':
      return { label: 'Click me', href: '#', style: 'primary' };
    case 'spacer':
      return { height: 40 };
    case 'video':
      return { video_url: '' };
    case 'html':
      return { html: '<p>Custom HTML block</p>' };
    default:
      return {};
  }
}

export interface InspectorField {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'url' | 'select' | 'color';
  options?: { value: string; label: string }[];
}

export const INSPECTOR_FIELDS: Record<BlockType, InspectorField[]> = {
  section: [
    { key: 'background', label: 'Background Color', type: 'color' },
    { key: 'padding', label: 'Padding (px)', type: 'number' },
  ],
  columns: [
    {
      key: 'column_count',
      label: 'Columns',
      type: 'select',
      options: [
        { value: '2', label: '2' },
        { value: '3', label: '3' },
        { value: '4', label: '4' },
      ],
    },
  ],
  heading: [
    { key: 'text', label: 'Text', type: 'text' },
    {
      key: 'level',
      label: 'Level',
      type: 'select',
      options: [
        { value: '1', label: 'H1' },
        { value: '2', label: 'H2' },
        { value: '3', label: 'H3' },
      ],
    },
  ],
  text: [{ key: 'text', label: 'Text', type: 'textarea' }],
  image: [
    { key: 'image_url', label: 'Image URL', type: 'url' },
    { key: 'alt', label: 'Alt Text', type: 'text' },
  ],
  button: [
    { key: 'label', label: 'Label', type: 'text' },
    { key: 'href', label: 'Link URL', type: 'url' },
  ],
  spacer: [{ key: 'height', label: 'Height (px)', type: 'number' }],
  video: [{ key: 'video_url', label: 'Video Embed URL', type: 'url' }],
  html: [{ key: 'html', label: 'HTML', type: 'textarea' }],
};
