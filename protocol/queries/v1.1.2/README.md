# Search Query Pack v1.1.2

This is a one-factor recall ablation of `v1.1.1`. The only query change is the
addition of `metabolite` to the metabolomics-layer vocabulary in pairwise
branches. This captures studies that use metabolite GWAS or circulating-
metabolite panels without calling the data `metabolomics` in the abstract.

The term is not added to the explicit multi-omics branch and does not satisfy
the review query alone: a second molecular layer, exact aging construct, and
formal causal-design anchor remain mandatory.

Springer Nature remains excluded from identification. PubMed, Scopus, Europe
PMC, Semantic Scholar, and manual Google Scholar remain unchanged from
`v1.0.0` pending their separate quality review.

`v1.1.2` remains a calibration query pack until branch quality and candidate
recall have been assessed.
