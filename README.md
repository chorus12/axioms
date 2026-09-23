# axioms
Аксиомы и теоремы программной инженерии

- Страница: https://chorus12.github.io/axioms/ — исходник `index.html`.
- Текстовая версия для агентов: `axioms.md`. Генерируется из `index.html`, руками не правится:

  ```bash
  python3 build_md.py index.html > axioms.md   # нужен pandoc
  ```

`.nojekyll` отключает Jekyll на GitHub Pages: без него `axioms.md` отдавался бы сконвертированным в HTML, а не исходным текстом.
