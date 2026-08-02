# Search Query Pack v1.1.1

This is a one-factor ablation of `v1.1.0`. The only query change is the OpenAlex
aging filter:

```text
title_and_abstract.search:aging|...
```

becomes:

```text
title_and_abstract.search.exact:aging|...
```

The change prevents OpenAlex stemming from treating generic uses of `age`,
such as `the genomics age`, as an aging-process signal. The six multi-omics
branches, formal causal-design anchors, abstract requirement, date limit, work
types, and retraction filter are unchanged.

Springer Nature remains excluded from identification. PubMed, Scopus, Europe
PMC, Semantic Scholar, and manual Google Scholar remain unchanged from
`v1.0.0` pending their separate quality review.

`v1.1.1` remains a calibration query pack until branch quality and candidate
recall have been assessed.
