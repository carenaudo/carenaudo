// KaTeX initialisation, loaded only on pages that set `[extra] math = true`.
//
// This lives in its own file rather than an inline `onload` attribute so the
// delimiters are plain JavaScript, not backslashes nested inside an HTML
// attribute inside a Tera template.
//
// Loaded with `defer` after auto-render.min.js, so it runs once the parser has
// finished and that script has executed.
//
// Delimiters are `$$...$$` and `$...$`. The LaTeX-style `\(...\)` is not used:
// Markdown eats the backslash before the parenthesis, so it never reaches
// KaTeX. The trade-off is that a literal dollar sign in prose on a math page
// needs escaping as `\$`.
renderMathInElement(document.body, {
  delimiters: [
    // $$ must come first, or $ would match its opening pair.
    { left: "$$", right: "$$", display: true },
    { left: "$", right: "$", display: false }
  ],
  // A malformed expression should render as red source text rather than
  // throwing and leaving the rest of the page unprocessed.
  throwOnError: false
});
