## What am I looking at?

This is the repository for my personal website: research notes (currently my master's thesis), projects, and trips. Each of the three sections has its own accent colour. See [rebuild.md](rebuild.md) for how the site is put together and how the old WordPress travel blog was imported.


## Writing a post

```sh
hugo new content research/my-post-title.md           # a research post
hugo new content trips/short-trips/my-weekend.md     # a short trip
hugo new content trips/norway-2024/tag-42.md         # a day of a multi-day trip
hugo new content projects/my-project.md              # a project page (bricks)
hugo server -D                                       # preview at http://localhost:1313, drafts included
```

Each command starts from the matching file in `archetypes/`. Set `draft: false` when the post is ready. Give thesis posts `tags: [thesis]`; the research page's tag filter relies on that tag. Pushing to `main` deploys the site via GitHub Actions.

Photos live in the media bucket at `site-media.oppernik.de`, not in this repository. Prepare them with `python3 tools/media/optimize.py <folder> <out> --prefix trips/<trip>`, upload `<out>` to the bucket, and refer to them by key: `{{< photo src="trips/<trip>/01.jpg" caption="…" >}}`.

`hugo server` also renders the theme's documentation at `/docs/` as a local reference. It is not part of the published site.

## Contact form

The form posts to [Formspree](https://formspree.io), because GitHub Pages can't run server-side code. Put your form id into `action` in `data/en/contactform.yaml`.


## Credits

The website uses [Hugo](https://gohugo.io/) along with the free website theme [Hugobricks](https://github.com/jhvanderschee/hugobricks_v2).

From Joost van der Schee:
The functionality is inspired by the many [Gutenberg Block Plugins](https://wpastra.com/plugins/wordpress-gutenberg-block-plugins/) that are available online. The design is based on the MIT licensed [Hugoplate from Zeon Studio](https://github.com/zeon-studio/hugoplate.git). The fonts and icons are Apache Licensed and come from [Google Fonts](https://fonts.google.com) and [Google Material Symbols](https://fonts.google.com/icons). The illustrations are free to use but require [an attribution to Storyset](https://storyset.com/terms). The social media icons (Facebook, Instagram, etc) belong to the respective social networks/their owners.