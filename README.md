## What am I looking at?

This is the repository for my static website, where I intend to publish short posts about my research, currently my master's thesis.


## Writing a post

```sh
hugo new content posts/my-post-title.md   # creates a draft
hugo server -D                            # preview at http://localhost:1313, drafts included
```

Set `draft: false` when the post is ready. Give thesis posts `tags: [thesis]`; the blog's tag filter and the thesis page rely on that tag. Pushing to `main` deploys the site via GitHub Actions.

`hugo server` also renders the theme's documentation at `/docs/` as a local reference. It is not part of the published site.

## Contact form

The form posts to [Formspree](https://formspree.io), because GitHub Pages can't run server-side code. Put your form id into `action` in `data/en/contactform.yaml`.


## Credits

The website uses [Hugo](https://gohugo.io/) along with the free website theme [Hugobricks](https://github.com/jhvanderschee/hugobricks_v2).

From Joost van der Schee:
The functionality is inspired by the many [Gutenberg Block Plugins](https://wpastra.com/plugins/wordpress-gutenberg-block-plugins/) that are available online. The design is based on the MIT licensed [Hugoplate from Zeon Studio](https://github.com/zeon-studio/hugoplate.git). The fonts and icons are Apache Licensed and come from [Google Fonts](https://fonts.google.com) and [Google Material Symbols](https://fonts.google.com/icons). The illustrations are free to use but require [an attribution to Storyset](https://storyset.com/terms). The social media icons (Facebook, Instagram, etc) belong to the respective social networks/their owners.