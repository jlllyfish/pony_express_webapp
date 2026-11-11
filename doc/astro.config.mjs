import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
    site: 'https://multi-coop.github.io',
    base: '/ponyexpress',
    integrations: [
        starlight({
            title: 'PonyExpress-DOC',
            social: {
                github: 'https://github.com/withastro/starlight',
            },
            sidebar: [
                {
                    label: 'Tutoriels',
                    autogenerate: { directory: 'tutorial' },

                    // items: [
                        // Each item here is one entry in the navigation menu.
                       // { label: 'Example Guide', link: '/guides/example/' },
                    //],
                },
                {
                    label: 'Guides',
                    autogenerate: { directory: 'guide' },

                    // items: [
                        // Each item here is one entry in the navigation menu.
                       // { label: 'Example Guide', link: '/guides/example/' },
                    //],
                },
                {
                    label: 'Références',
                    autogenerate: { directory: 'reference' },
                },
                {
                    label: 'Explications',
                    autogenerate: { directory: 'explanation' },
                },
            ],
        }),
    ],
});
