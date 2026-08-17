# Multi-omics integration across 101 causal-aging reports

## Executive conclusion

Multi-omics deserves a main Results section, but not a modality-by-modality catalogue. Across the 101 reports, the important distinction is how layers enter the analytic and causal workflow. The dominant architecture is a sequential workflow in which one or more broad assays nominate a candidate, another layer refines or localizes it, and a perturbation supplies the actual causal leverage. A smaller group performs material joint cross-layer integration. Another substantial group profiles layers in parallel and calls their concordance "integration." Cross-dataset QTL/Mendelian randomization (MR) studies form a distinct computational architecture, while a true paired single-cell multiome is rare.

The simplest useful Results structure is therefore:

1. **Layer landscape:** report-level layer combinations and assay provenance.
2. **Integration architecture:** joint, sequential, parallel, cross-dataset QTL/MR, and paired single-cell multiome.
3. **Causal contribution:** what each layer nominated, localized, mediated, triangulated, or merely validated.

This should be one compact main Results section, supported by an UpSet-style combination plot and one architecture-by-layer-role table. The article should not imply that adding layers itself strengthens causal identification. In most reports, causal leverage comes from randomization, genetic instruments, temporal intervention, or targeted perturbation; multi-omics chiefly improves target selection, mechanistic localization, and triangulation.

## Scope and analytic boundary

I used the three requested corpus-pack files:

- `eligible_graph_manifest_101.csv` to resolve the canonical graph and deterministic Docling Markdown for all 101 reports;
- `eligible_graph_profiles_101.jsonl` to create an initial, report-level candidate inventory of normalized layers, assay names, data origin, and evidence locations;
- `corpus_graph_summary.json` to check corpus totals and methodological boundaries.

The Luna Light graph was used only for orientation and stratification. I did not treat graph labels, `identification_status`, design families, or causal levels as adjudicated truth. I checked canonical full text for 40 reports, exceeding the requested minimum of 25. The audit deliberately covered common combinations, all seven reports that collapse to one normalized layer, five-layer combinations, QTL/MR reports, gut-microbiome-metabolite studies, single-cell claims, and reports in which qPCR or western blotting had been represented as an omics layer.

This is report-level exploratory article-structure analysis. It does not revise eligibility, PRISMA counts, study linkage, or final causal levels.

### Operational definitions

- **Joint integration:** individual features, modules, pathways, or predictions from at least two layers enter the same cross-layer model, overlap, network, correlation structure, or explicit performance comparison.
- **Sequential omics-to-candidate-to-perturbation:** omics nominates or refines a target, after which a gene, protein, metabolite, microbe, drug, or pathway is perturbed.
- **Parallel descriptive profiling:** layers are analyzed separately against the same age, disease, or intervention contrast, followed primarily by narrative or pathway-level concordance.
- **Cross-dataset QTL/MR integration:** GWAS and one or more eQTL, mQTL, pQTL, sQTL, TWAS, or metabolomic resources are linked through MR, SMR, colocalization, or related summary-data methods.
- **Paired single-cell multiome:** two or more molecular modalities are measured in the same cell or nucleus. Single-cell assays run on different cells, and scRNA-seq combined with spatial or bulk RNA-seq, do not meet this definition.
- **Validation-only layer:** targeted qPCR, western blot, ELISA, immunostaining, or a similarly narrow assay confirms an omics-derived target but does not provide a genome-scale layer.
- **Peripheral multi-omics:** the paper uses the label but the substantive analysis is one normalized layer, multiple platforms within one layer, or a multi-omics component that is not central to the causal claim.

The architecture categories overlap. For example, a study can jointly integrate microbiome and metabolome data, then perturb the selected microbe and metabolite. Prevalence estimates below are therefore non-exclusive.

## Quantitative layer landscape

### Candidate normalized-layer inventory for all 101 reports

The graph-derived inventory contains 37 distinct exact combinations. Ninety-four reports (93.1%) have at least two distinct normalized layers; seven (6.9%) collapse to one normalized layer. Reports contain:

| Distinct normalized layers | Reports | Percent |
|---:|---:|---:|
| 1 | 7 | 6.9% |
| 2 | 30 | 29.7% |
| 3 | 38 | 37.6% |
| 4 | 21 | 20.8% |
| 5 | 5 | 5.0% |

Layer presence, after deduplicating repeated nodes within a report, is:

| Normalized layer | Reports | Percent |
|---|---:|---:|
| Transcriptomics | 90 | 89.1% |
| Proteomics | 60 | 59.4% |
| Metabolomics | 46 | 45.5% |
| Epigenomics | 35 | 34.7% |
| Genomics | 21 | 20.8% |
| Other molecular omics | 15 | 14.9% |
| Lipidomics | 11 | 10.9% |
| Microbiomics | 9 | 8.9% |
| Metagenomics | 3 | 3.0% |

These are evidence-location candidate counts, not corrected assay adjudications. In particular, transcriptomics and proteomics are over-inclusive because some nodes are targeted expression or protein validation.

### Exact combinations occurring at least twice

Nineteen exact combinations account for 83 reports; the ten most frequent account for 60.

| Candidate exact combination | Reports |
|---|---:|
| Proteomics + transcriptomics | 9 |
| Metabolomics + proteomics + transcriptomics | 8 |
| Epigenomics + genomics + proteomics + transcriptomics | 6 |
| Metabolomics + transcriptomics | 6 |
| Transcriptomics only | 6 |
| Epigenomics + transcriptomics | 6 |
| Epigenomics + proteomics + transcriptomics | 5 |
| Lipidomics + proteomics + transcriptomics | 5 |
| Metabolomics + proteomics | 5 |
| Genomics + transcriptomics | 4 |
| Epigenomics + metabolomics + proteomics + transcriptomics | 4 |
| Metabolomics + microbiomics + transcriptomics | 4 |
| Epigenomics + other molecular omics + transcriptomics | 3 |
| Epigenomics + other molecular omics + proteomics + transcriptomics | 2 |
| Lipidomics + metabolomics + transcriptomics | 2 |
| Metabolomics + other molecular omics + transcriptomics | 2 |
| Epigenomics + metabolomics + transcriptomics | 2 |
| Epigenomics + genomics + transcriptomics | 2 |
| Genomics + proteomics + transcriptomics | 2 |

The remaining 18 reports each occupy a unique exact combination. Those rare combinations include proteomics only; several four- and five-layer QTL/MR configurations; microbiome/metagenome-metabolome-proteome configurations; glycomic/cytomic configurations; and lipidomic combinations. This long tail is real as an assay-description phenomenon, but it is too sparse for article subsections organized by exact combination.

The strongest pairwise co-presences are proteomics-transcriptomics (50 reports), metabolomics-transcriptomics (36), epigenomics-transcriptomics (34), metabolomics-proteomics (27), epigenomics-proteomics (20), and genomics-transcriptomics (20). These six relationships capture the main combinatorial backbone.

### What the raw combinations overstate or miss

Full-text checks show that exact layer sets are not equivalent to integration depth:

- **Targeted validation can inflate layer count.** In *Medicago Sativa L. Saponin-Driven Lactobacillus Intestinalis Restores Intestinal Stemness...* (DOI 10.1002/advs.202515370), the broad discovery layers are 16S microbiome profiling and targeted bile-acid metabolomics. qRT-PCR and western blot in sections 2.5-2.6 validate FXR-Wnt signaling; they are not transcriptome- and proteome-wide layers.
- **A single normalized layer can contain multiple informative platforms.** *Spatiotemporal mapping reveals Ccl8hi macrophages...* (DOI 10.1002/ctm2.70527) combines bulk RNA-seq, scRNA-seq, and spatial transcriptomics, but all are transcriptomic. Likewise, *Multiomic identification of senescent stem cell populations...* (DOI 10.1126/sciadv.adu2294) combines single-cell, spatial, and bulk transcriptomics.
- **Post-translational depth is collapsed.** *Gestational exposure to PP-NPs...* (DOI 10.1016/j.jhazmat.2026.142949) uses global proteomics and phosphoproteomics (sections 2.3 and 2.5), but both normalize to proteomics.
- **A protein assay is not automatically proteomics.** In *Multi-omic rejuvenation and lifespan extension upon exposure to youthful circulation* (DOI 10.1038/s43587-023-00451-9), the broad layers are RRBS/methylation arrays and RNA-seq. Western blots are explicitly described as validation in “Protein, western blotting and RT-qPCR mRNA expression.”
- **The canonical Markdown can be incomplete.** The path for *A senescence-based machine learning model prognosticates and personalizes therapy in cervical cancer* (DOI 10.21037/tcr-2026-1-0264) contains supplementary figure legends rather than the full article, so its one-layer graph profile cannot support a strong integration classification.

## Integration architectures and prevalence

### 1. Joint cross-layer integration

**Approximate prevalence:** about 20-30 of 101 reports, depending on whether simple feature intersection or pathway overlap is counted as joint integration. A stricter definition requiring a cross-layer model, correlation network, or explicit single- versus multi-layer comparison yields the lower end.

**Typical layer roles:** one layer provides candidate regulators or states; another supplies downstream molecular consequences; a third can anchor the network to a phenotype. In predictive studies, all layers are co-predictors. In microbiome studies, taxa are upstream candidate exposures, metabolites are candidate mediators, and host transcript/protein changes are downstream responses.

**What it adds beyond one layer:** cross-layer integration can identify a feature or pathway that is weak in each layer but coherent across layers; separate regulatory from functional readouts; connect compartments such as gut and cochlea; or demonstrate incremental predictive performance over single-layer models.

Representative full-text examples:

- *StackAge: an ensemble-based clock for precise quantification of biological age using multi-omics data* (DOI 10.1093/bib/bbag271), “Data collection and preprocessing” and “Feature selection and model evaluation.” Proteins and metabolites enter the same prediction model. The integrated model reached a reported age correlation of about 0.93, compared with 0.86 for proteins and 0.53 for metabolites alone. Here, proteomics carries most predictive signal and metabolomics adds modest incremental information. This is one of the clearest demonstrations of added value over a single layer.
- *Gut-Metabolome-Proteome Interactions in Age-Related Hearing Loss* (DOI 10.1002/advs.202514269), sections 2.6 and 4.13. Metagenomic taxa, cochlear metabolites, and cochlear proteins are linked by FDR-filtered Spearman networks and shared KEGG pathways. Metabolites, especially 5-HTP, bridge gut taxa and cochlear protein responses. Integration adds a cross-compartment mediator hypothesis that no single layer supplies.
- *Multiomic profiling of the liver across diets and age in a diverse mouse population* (DOI 10.1016/j.cels.2021.09.005), “Multiomic molecular analysis of the aging liver.” The study reports 274 mice with complete transcript, protein, and metabolite data, allowing matched cross-layer comparisons across strain, diet, age, and sex. Integration adds separation of genotype-, diet-, and age-associated variance and exposes mRNA-protein discordance and non-consensus networks.
- *Multi-Omics Analysis Reveals Biomarkers... Therapeutic Plasma Exchange* (DOI 10.1111/acel.70103), sections 2.4-2.5 and 4.5. Changes in cytomic, glycomic, lipidomic, metabolomic, and proteomic features are related to epigenetic age changes, followed by inter-omics correlations. The layers mainly act as candidate response markers around an epigenetic-clock outcome. Integration adds coordinated response characterization and baseline responder signals, although the cohort is small and the analysis is primarily correlational.
- *Multi-Omics Analysis Reveals Photodynamic Therapy Ameliorating Skin Photoaging...* (DOI 10.1111/acel.70328), sections 2.2 and 3.4. RNA and protein changes are intersected, and transcript-metabolite pathway analysis centers the mechanism on glucose metabolism and citrate. Integration adds convergence on a metabolic mechanism; the intervention and subsequent targeted experiments, not the intersection itself, carry causal weight.
- *The Age-Dependent Resident Myonuclear Multi-Omic Response...* (DOI 10.1002/advs.202521633), sections 2.7-2.9. BETA analysis links myonuclear methylation changes to bulk and single-nucleus expression. This adds a regulatory interpretation to age-dependent transcriptional responses, but the modalities are not a paired single-nucleus multiome.

### 2. Sequential omics-to-candidate-to-perturbation workflows

**Approximate prevalence:** about 45-55 reports. This is the largest architecture. A broader screen finds intervention or direct-perturbation components in many more reports, but only this range clearly uses omics upstream of target selection or mechanistic refinement.

**Typical layer roles:** transcriptomics often nominates genes or cell states; epigenomics identifies regulatory control; proteomics identifies interactions or downstream pathway activity; metabolomics supplies a candidate mediator; microbiome/metagenome data nominate organisms or functions. The causal link is then tested by knockdown, knockout, overexpression, inhibitor, metabolite supplementation, microbial transfer, or genetic epistasis.

**What it adds beyond one layer:** the added value is not generic "systems biology." It is search-space reduction and mechanistic chaining: from state to candidate, candidate to molecular consequence, and molecular consequence to intervention-sensitive phenotype.

Representative full-text examples:

- *ATF3 Deficiency Exacerbates Ageing-Induced Atherosclerosis and Clinical Intervention Strategy* (DOI 10.1002/advs.202502249), Abstract and sections 2.2-2.6. Human scRNA-seq nominates ATF3 in vascular smooth muscle cells; RNA-seq and CUT&Tag connect ATF3 to ATG7 transcription; pull-down mass spectrometry identifies ATG7 interaction; m6A analyses suggest regulation of Atf3 stability; ATF3 knockdown and terazosin experiments test dependence. Each layer has a distinct role, while perturbation supplies the causal evidence.
- *Inhibition of MyD88 in Tubular Epithelial Cells...* (DOI 10.1007/s10753-026-02526-2), “Differentially Expressed Genes Identified by Integrated Transcriptomic and Proteomic Analyses.” Independent transcriptomic and proteomic datasets are intersected, a PPI module and literature review prioritize MyD88, and cell-specific inhibition tests the candidate. Integration adds reproducibility across molecular levels before perturbation.
- *Medicago Sativa L. Saponin-Driven Lactobacillus Intestinalis...* (DOI 10.1002/advs.202515370), sections 2.2, 2.5, and 2.6. 16S profiling nominates *L. intestinalis*; bile-acid metabolomics nominates UDCA; bacterial culture, antibiotics, microbial administration, UDCA treatment, and FXR/Wnt measurements form a microbe-to-metabolite-to-host pathway. The transcript and protein assays are targeted validation, not discovery layers.
- *Aged Gut Microbiota Contributes to Cognitive Impairment...* (DOI 10.1111/acel.70064), Abstract and sections 2.2-2.4. Fecal transfer establishes that an aged microbiota can transmit a phenotype; metagenomics and metabolomics nominate *Bifidobacterium pseudolongum* and indoleacetic acid; hippocampal proteomics characterizes the host response; organism, metabolite, and AhR-dependent experiments refine the mechanism. Multi-omics adds mediator discovery between the transferred exposure and neural phenotype.
- *Restoration of energy homeostasis by SIRT6 extends healthy lifespan* (DOI 10.1038/s41467-021-23545-7), results and “Liver proteomics.” Transcript, protein, and metabolite changes characterize the energetic state of SIRT6-manipulated mice; genetic manipulation and lifespan/healthspan outcomes provide the intervention. The layers mainly explain how the perturbation changes energy homeostasis.
- *NFYB-1 regulates mitochondrial function and longevity via lysosomal prosaposin* (DOI 10.1038/s42255-020-0200-2), Extended Data Fig. 3. Transcriptomics and proteomics identify altered candidates in *nfyb-1* and *isp-1* backgrounds; RNAi of selected proteins identifies *spp-8* as a lifespan modifier. Integration reduces the candidate set; RNAi supplies the functional test.
- *Multi-omics and experimental evidence... identify caspase-8... in osteoarthritis* (DOI 10.1186/s12964-026-02985-y), “Public transcriptomic and single-cell analyses,” “Proteomics analysis,” “Integrated proteomic analysis...,” and “Mendelian randomization analysis.” Public bulk/single-cell/spatial RNA data localize CASP8 programs, proteomics measures response to caspase-8 inhibition, QTL/MR offers population-level support, and inhibitor/siRNA assays test mechanism. This is a hybrid sequential plus cross-dataset design.
- *Unraveling the Key Pathways through Cordycepin Prolongs Lifespan...* (DOI 10.26599/fshw.2026.9251125), Abstract and Introduction aims. Transcriptomics, metabolomics, and microbiome modeling converge on IIS/FOXO; daf-2/daf-16 genetics and DAF-16 localization test pathway dependence. The omics layers broaden and connect the response; functional genetics establishes the relevant pathway.

### 3. Parallel descriptive profiling

**Approximate prevalence:** about 20-30 reports. These reports often use matched experimental contrasts but analyze each layer separately, then describe shared reversal, enrichment, or rejuvenation.

**Typical layer roles:** each layer is a separate readout of an intervention or age contrast. One may be a primary outcome, such as epigenetic age, while other layers contextualize the response. Different layers may come from different tissues, cohorts, or species.

**What it adds beyond one layer:** breadth and triangulation. Parallel profiling can show that a treatment is not confined to one molecular level, reveal tissue- or cell-type specificity, and distinguish concordant from discordant responses. It generally does not identify a cross-layer mechanism unless followed by a network or perturbation analysis.

Representative full-text examples:

- *Multi-omics profiling reveals systemic rejuvenation of the aged kidney through senolytic therapy* (DOI 10.1038/s41536-026-00490-x), Abstract and “Proteomic profiling reveals the reversal of renal aging...”. Single-cell transcriptomics resolves cell-specific aging signatures; bulk kidney proteomics describes pathway changes. The reported cross-omics PCA supports broad concordance, but the main analyses remain layer-specific. Integration adds cell localization to a bulk protein response.
- *Multi-omic rejuvenation and lifespan extension upon exposure to youthful circulation* (DOI 10.1038/s43587-023-00451-9), Abstract, RNA-seq analysis, and protein/western-blot validation. Methylation clocks and RNA-seq independently indicate rejuvenation; protein measurements validate selected transcripts. The layers triangulate a broad response but do not form a joint model.
- *Multi-Omics Reveals Mechanisms of Metabolic Rejuvenation... by Losartan* (DOI 10.1111/acel.70498), sections 3.1 and 3.2. Serum metabolomics and cardiac proteomics each construct an aging signature and compare it with losartan response. The layers are in different biological compartments; they support systemic generality rather than a measured metabolite-to-protein chain.
- *Sleep chart of biological ageing clocks in middle and late life* (DOI 10.1038/s41586-026-10524-5), Abstract, “Proteome-wide associations,” “Metabolome-wide associations,” and “Genetic analyses.” Imaging, proteomic, and metabolomic biological-age clocks are compared across sleep duration; genetics addresses related questions. The layers broaden organ and molecular coverage, but they are primarily parallel clocks rather than a fused molecular model.
- *Multi-omics profiling reveals systemic rejuvenation...* and the losartan report also show why "parallel" is not a criticism: a consistent intervention-associated reversal across molecular levels is valuable, but it should be reported as triangulation rather than joint integration.

### 4. Cross-dataset QTL/MR integration

**Approximate prevalence:** 14 of 101 reports have a graph-nominated genetic-instrument analysis, and representative full-text checks support approximately 12-14 as genuine cross-dataset QTL/MR architectures. The exact number should be finalized from the review extraction, not the graph.

**Typical layer roles:** genomics supplies instruments and outcome GWAS; eQTL/mQTL/pQTL/sQTL resources represent genetically proxied expression, methylation, protein abundance, or splicing; TWAS prioritizes gene expression; colocalization tests whether molecular and outcome associations may share a signal. Differential expression or tissue assays commonly provide non-causal validation.

**What it adds beyond one layer:** molecular prioritization from GWAS loci, directionally oriented hypotheses, tissue or molecular-level triangulation, and filtering through colocalization. It does not measure a within-person multi-omic mechanism, and QTL labels should not be interpreted as direct molecular observations.

Representative full-text examples:

- *A trans-omic Mendelian randomization study of parental lifespan...* (DOI 10.1111/acel.13497), sections 2.4, 2.7, and 4.2-4.6. TWAS, proteome-wide MR, metabolome-wide MR, phenome-wide MR, and multi-trait colocalization prioritize eGenes, eProteins, and eMetabolites. Genomics is the instrument substrate; the other layers are genetically proxied exposures. Integration adds cross-layer target prioritization and adverse/beneficial phenome mapping.
- *Investigating the causal role of cellular senescence-related genes in preeclampsia* (DOI 10.3389/fendo.2025.1661666), Abstract, “Data sources,” and “mQTL-eQTL integration analysis.” Preeclampsia GWAS is linked to eQTL, mQTL, and pQTL through SMR/HEIDI and colocalization; placental RT-PCR is preliminary expression support. The cross-layer result is a set of regulatory hypotheses, not direct placental mediation.
- *Multi-omics data reveal causal associations... in rheumatoid arthritis* (DOI 10.1097/md.0000000000047376), sections 3.1-3.4. Separate mQTL-, eQTL-, and pQTL-to-RA analyses are followed by mQTL-eQTL and eQTL-pQTL linking. The added value is regulatory ordering and consistency across molecular proxies.
- *Depletion of loss-of-function germline mutations in centenarians reveals longevity genes* (DOI 10.1038/s41467-024-52967-2), “Mendelian randomization” and “Multi-omic analysis of the identified longevity-associated genes.” Exome sequencing nominates rare-variant genes; blood eQTL MR and age associations in expression, methylation, and plasma protein datasets characterize them. Most added layers are follow-up characterization of exome-derived candidates.
- *Major Psychiatric Disorders, Substance Use Behaviors, and Longevity* (DOI 10.1001/jamapsychiatry.2024.1429), “Data Sources,” “Transcriptomic Imputation,” and druggable-genome cis-instrument MR sections. GWAS instruments estimate associations with longevity and epigenetic age; TWAS and cortical pQTL analyses prioritize smoking-related mechanisms and targets. The layers extend a genetic-liability analysis rather than forming a measured biological cascade.
- *Multi-omic underpinnings of epigenetic aging and human longevity* (DOI 10.1038/s41467-023-37729-w), “TWASs reveal transcriptomic architecture...,” metabolome-wide MR, and drug-target MR. The main gain is systematic mapping from GWAS-defined aging traits to predicted expression and metabolites.

### 5. Single-cell multiome versus multi-omics containing single-cell data

**Approximate prevalence:** 30 reports have a graph evidence candidate involving single-cell, single-nucleus, single-myonucleus, or spatial data. Only one audited report is an unambiguous paired single-cell multiome. One additional report performs multiple omics at single-oocyte resolution but on different oocytes. Most of the remainder add scRNA-seq or spatial transcriptomics to bulk or targeted assays.

**Typical layer roles:** single-cell transcriptomics localizes age or senescence programs to cell types and states; spatial transcriptomics adds anatomical context; paired ATAC-RNA connects accessibility and expression in the same nucleus; single-cell proteomics can expose RNA-protein discordance.

**What it adds beyond one layer:** resolution of cellular heterogeneity, avoidance of bulk composition confounding, spatial localization, and, only in paired multiome designs, within-cell regulatory coupling.

Representative full-text examples:

- **True paired multiome:** *Multiomic single-cell perturbation screens reveal critical lncRNA regulators of senescence* (DOI 10.1038/s43587-026-01100-7), Abstract and Extended Data Figs. 2 and 4. CRISPRi perturbations are coupled to simultaneous single-nucleus RNA and chromatin accessibility. RNA modules are outcomes, ATAC modules provide regulatory context, and perturbation anchors direction. This is qualitatively different from merely combining separate single-cell datasets.
- **Multiple single-cell assays, not paired modalities:** *Single-Cell Multi-Omics Analysis of In Vitro Post-Ovulatory-Aged Oocytes...* (DOI 10.1016/j.mcpro.2024.100882), “Single-Cell Multi-Omics Profiling...”. Nine oocytes per group undergo proteome/phosphoproteome profiling, while seven different oocytes per group undergo Smart-seq2. Cross-layer comparison reveals weak RNA-protein correspondence and protein degradation, but it is not same-cell RNA-protein pairing.
- **Separate single-cell modalities:** *Midkine as a driver of age-related changes and increase in mammary tumorigenesis* (DOI 10.1016/j.ccell.2024.09.002), Summary and “Single-cell profiles of the rat mammary gland at different ages.” scRNA-seq and scATAC-seq are generated with separate 10x kits and compared across the same age groups; they are not simultaneous measurements in the same cells.
- **Single-cell plus separate epigenome:** *The Age-Dependent Resident Myonuclear Multi-Omic Response...* (DOI 10.1002/advs.202521633), sections 2.7-2.9. smnRNA-seq localizes expression states; RRBS is performed separately and linked through regulatory analysis.
- **Several transcriptomic resolutions:** *Spatiotemporal mapping reveals Ccl8hi macrophages...* (DOI 10.1002/ctm2.70527), Abstract and methods 2.5-2.10, combines bulk, single-cell, and spatial RNA data. It is a strong multiresolution transcriptomics workflow, not a multi-layer multiome.

### 6. Validation-only layers and peripheral multi-omics

**Approximate prevalence:** at least 10-15 reports contain a layer that is principally targeted validation rather than an omics-wide analysis. A broad graph-node scan flags 22 candidates, but some are genuine targeted omics or are false positives, so 10-15 is the defensible full-text-based range. Seven reports collapse to a single normalized layer; about 7-12 reports are plausibly peripheral or within-layer "multi-omics" cases.

**Typical layer roles:** qPCR validates selected RNA changes; western blot or immunostaining validates protein abundance or localization; targeted metabolite assays verify a nominated mediator; external single-cell data localize a candidate selected elsewhere.

**What it adds beyond one layer:** orthogonal confirmation and biological localization. It should not increase the number of discovery-scale omics layers in the synthesis.

Representative full-text examples:

- *Medicago Sativa L. Saponin-Driven Lactobacillus Intestinalis...* (DOI 10.1002/advs.202515370), sections 2.5-2.6: qRT-PCR and immunoblotting confirm FXR/Wnt effects after the microbiome-metabolite discovery chain.
- *Exercise Remodels Akkermansia-Associated Eicosanoid Metabolism...* (DOI 10.3390/microorganisms13061379), Abstract and section 2.4: the substantive two-layer integration is 16S plus untargeted metabolomics; qRT-PCR measures selected senescence and barrier markers.
- *Multi-omic rejuvenation and lifespan extension upon exposure to youthful circulation* (DOI 10.1038/s43587-023-00451-9): western blotting confirms selected RNA-level observations and should not be counted as a proteome layer.
- *Investigating the causal role... in preeclampsia* (DOI 10.3389/fendo.2025.1661666): RT-PCR in 15 placentas is preliminary validation of summary-data candidates, not a transcriptomic discovery layer.
- *Multi-Omics Analysis and Validation... in NAFLD* (DOI 10.2147/jir.s525168), “Data Sources,” “Summary-Data-Based MR Analysis,” and “Validation of Candidate Genes”: qRT-PCR validates candidates from QTL/GWAS analyses.

Peripheral and boundary examples:

- *NHE7 drives endometrial cancer progression...* (DOI 10.1038/s42003-025-08296-1), Abstract and “Increased NHE7 expression...”. The paper calls the workflow multi-omics, but the discovery analysis is TCGA RNA-seq plus clinical data; subsequent protein assays are targeted mechanistic measurements. Multi-omics is peripheral to the actual candidate-to-perturbation chain.
- *Gestational exposure to PP-NPs...* (DOI 10.1016/j.jhazmat.2026.142949), sections 2.3 and 2.5, is rich in proteome and phosphoproteome information but remains one normalized molecular layer. Its value is post-translational depth, which a simple layer count hides.
- *Activation of LAMP1-mediated lipophagy...* (DOI 10.1016/j.jot.2025.05.010), section 3.3, integrates scRNA-seq and bulk RNA-seq with machine learning. This is cross-dataset, multiresolution transcriptomics followed by perturbation, not cross-layer multi-omics.
- *Vaccarin ameliorates osteoarthritis...* (DOI 10.1016/j.phymed.2025.156697), “RNA sequencing analysis,” uses transcriptomics to nominate a pathway and targeted experiments to test it. The multi-omics component is not central.
- *A senescence-based machine learning model... in cervical cancer* (DOI 10.21037/tcr-2026-1-0264) cannot be classified confidently from the canonical Markdown because only supplementary figure legends are present. This is a document-completeness blind spot, not evidence for reclassification.

## Causal role by layer

The same layer has different causal meaning across architectures. The synthesis should record role, not only presence.

| Layer | Common roles in these reports | What it can add | What it does not establish by itself |
|---|---|---|---|
| Genomics/GWAS | Instrument source, outcome association, rare-variant candidate nomination, genotype context | Directionally oriented hypotheses; inherited perturbation; locus prioritization | A measured molecular mechanism in the study sample |
| Epigenomics | Regulatory state, aging-clock outcome, candidate mediator, chromatin-accessibility response | Regulatory localization; persistent aging readout; candidate ordering with expression | Causality from methylation/accessibility to phenotype without a valid design |
| Transcriptomics | Candidate genes, pathways, cell states, spatial localization, perturbation response | High-coverage discovery and cell-type specificity | Protein activity, metabolite flux, or functional necessity |
| Proteomics/phosphoproteomics | Functional abundance, interaction partners, signaling state, perturbation response | RNA-protein discordance; interaction and kinase-pathway refinement | Necessity or sufficiency without intervention |
| Metabolomics/lipidomics | Candidate mediator, systemic response, pathway flux proxy, aging signature | Small-molecule bridge between exposure and phenotype; intervention target | Direction of mediation from cross-sectional abundance alone |
| Microbiomics/metagenomics | Candidate organism/community exposure, functional potential | Host-microbe linkage; transmissible exposure candidates | Organism-specific causality without transfer, depletion, or supplementation |
| Single-cell/spatial | Cell-state or anatomical localization; composition-aware response | Heterogeneity and niche resolution | A second omics layer unless another modality is measured |
| Targeted validation assays | Orthogonal confirmation of selected molecules | Confidence that a nominated signal is measurable by another assay | A new discovery-scale omics layer |

## Do these patterns warrant a main Results section?

**Yes.** The reason is not merely that 94 graph profiles contain at least two normalized layers. The integration architecture changes what claim a report can support:

- joint models test cross-layer coherence or incremental prediction;
- sequential designs use omics to choose what is later perturbed;
- parallel profiling broadens and triangulates an intervention response;
- QTL/MR links molecular proxies across external datasets;
- paired single-cell multiome enables within-cell regulatory coupling;
- validation-only layers confirm but do not expand discovery breadth.

Without a dedicated Results section, these differences will be lost inside design-family or biological-topic summaries. Conversely, a long layer-by-layer section would duplicate familiar biology and obscure the actual analytic contribution.

### Simplest proposed structure

#### Results: How multiple omics layers entered the causal workflow

**Paragraph/subsection 1: Layer combinations and provenance.** Report the number of distinct candidate layers, the most frequent combinations, and whether layers were measured in-report or drawn from external datasets. Show one UpSet plot and note targeted-assay inflation.

**Paragraph/subsection 2: Integration architectures.** Present joint, sequential, parallel, and QTL/MR patterns, with paired single-cell multiome as a short callout. A single table should list architecture, approximate prevalence, typical layer roles, representative reports, and added value.

**Paragraph/subsection 3: Relationship to causal leverage.** State where causality actually enters: perturbation, intervention, genetic instrument, or temporal design. Contrast this with the contribution of multi-omics: nomination, localization, mediation hypothesis, convergence, or validation.

This structure is simpler and more defensible than subsections for transcriptomics, proteomics, metabolomics, and so on. It also directly supports the review's causal framing.

## Graph and extraction-template blind spots

1. **Assay scale is missing.** The graph can label qPCR, western blot, ELISA, or SELECT as transcriptomic, proteomic, or epigenomic layers. The template needs `assay_scope = genome_wide | targeted_panel | single_analyte | validation_only`.
2. **Sample alignment is missing.** It cannot distinguish same aliquot, same participant, partially overlapping cohort, different tissue from the same animal, independent external cohorts, or different single cells. Add `sample_alignment` and `biospecimen_alignment`.
3. **The integration operator is missing.** "Integrated" can mean feature concatenation, overlap, correlation, pathway concordance, multi-block latent factors, mediation, or narrative comparison. Add a controlled `integration_operator` field.
4. **Layer role is free text.** The template should encode `causal_role = exposure | instrument_source | candidate_nominator | mediator_candidate | outcome | effect_modifier | localization | perturbation_readout | validation_only`.
5. **Paired multiome is not represented.** Add `paired_modalities_within_unit`, with the unit specified as cell, nucleus, participant, animal, tissue, or cohort.
6. **Within-layer multimodality is collapsed.** scRNA-seq, spatial RNA, bulk RNA, proteome, phosphoproteome, and ubiquitome carry different information even when they share a normalized layer. Preserve both normalized layer and modality/sub-layer.
7. **`other_molecular_omics` is heterogeneous.** It currently mixes microRNA, glycomics, cytomics, and sometimes an "integrated multi-omics analysis" node. These require explicit modality names and should not be counted as a coherent layer.
8. **QTL semantics are ambiguous.** pQTL and eQTL data are both genomic association resources and proxies for protein/expression. The template should distinguish measured abundance from genetically predicted abundance.
9. **External-data provenance is too coarse.** `external_dataset_analyzed` does not capture ancestry, tissue, sample overlap, assay platform, or whether the dataset was used for discovery, replication, or annotation.
10. **Temporal order is missing.** The graph does not encode whether omics was measured before treatment, after treatment, at multiple time points, or only in a separate validation cohort.
11. **Document completeness can masquerade as biology.** The cervical-cancer canonical Markdown is supplementary-only, and some publisher-derived Markdown is a preview page. Add a document-completeness flag before interpreting absent layers.
12. **Report-study duplication is not handled at this level.** The published and preprint versions of the resident myonuclear study both appear as reports. That is appropriate for a report corpus, but article-level prevalence should be labeled report-level unless study families are linked.
13. **Graph evidence can confuse discovery with validation.** A layer count should be accompanied by the number of discovery-scale layers and the number of validation-only modalities.
14. **Integration quality is unmeasured.** Useful fields include cross-validation, independent test data, missing-data handling, batch harmonization, multiple-testing control, and whether single-omics baselines were compared.

## Full-text audit trail

The following 40 canonical Markdown reports were inspected. “Primary coding” summarizes the integration architecture for this analysis only; it does not alter eligibility or causal level.

| DOI | Short title | Primary coding | Full-text section/evidence checked |
|---|---|---|---|
| 10.1001/jamapsychiatry.2024.1429 | Psychiatric disorders, substance use, and longevity | Cross-dataset QTL/MR | Data Sources; Transcriptomic Imputation; MR Instruments |
| 10.1002/advs.202502249 | ATF3 deficiency and atherosclerosis | Sequential | Abstract; 2.2-2.6 |
| 10.1002/advs.202514269 | Gut-metabolome-proteome in hearing loss | Joint + sequential | 2.6; 4.13 |
| 10.1002/advs.202515370 | Saponin, *L. intestinalis*, UDCA, FXR-Wnt | Sequential; validation-only RNA/protein | 2.2; 2.5; 2.6 |
| 10.1002/advs.202521633 | Resident myonuclear response | Joint, separately measured modalities | 2.7-2.9; 4.9-4.10 |
| 10.1002/ctm2.70527 | Ccl8hi macrophages in testicular inflammaging | Within-layer multiresolution + sequential | Abstract; 2.5-2.10 |
| 10.1007/s10753-026-02526-2 | MyD88 in sepsis-associated kidney injury | Joint screen + sequential | Integrated transcriptomic/proteomic DEGs |
| 10.1016/j.cels.2021.09.005 | Liver across diets and age | Joint | Multiomic molecular analysis of the aging liver |
| 10.1016/j.ccell.2024.09.002 | Midkine and mammary tumorigenesis | Separate scRNA/scATAC + sequential | Summary; Single-cell profiles; resource table |
| 10.1016/j.jhazmat.2026.142949 | PP-NP trophoblast phosphoproteome | Within-layer multi-platform | 2.3; 2.5; 5.20-5.21 |
| 10.1016/j.jot.2025.05.010 | LAMP1-mediated lipophagy | Within-layer multiresolution + sequential | 3.3 |
| 10.1016/j.mcpro.2024.100882 | Single-oocyte RNA/protein/phosphoprotein | Parallel single-cell assays, not paired | Single-Cell Multi-Omics Profiling section |
| 10.1016/j.phymed.2025.156697 | Vaccarin in osteoarthritis | Peripheral/sequential | RNA sequencing analysis |
| 10.1038/s41438-020-00420-y | Pear fruit senescence | Joint | Compounds; mRNAs; microRNA-mRNA interactions |
| 10.1038/s41467-021-23545-7 | SIRT6 and healthy lifespan | Parallel + sequential | Results; Liver proteomics |
| 10.1038/s41467-023-37729-w | Epigenetic aging and longevity | Cross-dataset QTL/MR | TWAS; metabolomic MR; drug-target MR |
| 10.1038/s41467-024-52967-2 | Loss-of-function variants in centenarians | Cross-dataset follow-up | MR; multi-omic analysis of identified genes |
| 10.1038/s41536-026-00490-x | Senolytic rejuvenation of aged kidney | Parallel with limited joint check | Abstract; proteomic reversal section |
| 10.1038/s41586-026-10524-5 | Sleep chart of aging clocks | Parallel + genetic analysis | Abstract; ProWAS; MetWAS; genetic analyses |
| 10.1038/s42003-025-08296-1 | NHE7 in endometrial cancer | Peripheral/sequential | Abstract; NHE7 expression results; Methods |
| 10.1038/s42255-020-0200-2 | NFYB-1 and lysosomal prosaposin | Sequential | Extended Data Fig. 3 |
| 10.1038/s43587-023-00451-9 | Youthful circulation | Parallel; protein validation only | Abstract; RNA-seq; protein/western blot section |
| 10.1038/s43587-026-01100-7 | lncRNA Perturb-multiome | True paired single-cell multiome | Abstract; Extended Data Figs. 2, 4, 6, 8 |
| 10.1093/bib/bbag271 | StackAge | Joint predictive fusion | Abstract; preprocessing; model comparison |
| 10.1093/eurheartj/ehad361 | Atherosclerosis and epigenetic age | Parallel/concordance | Methylomics; unbiased proteomics; transcript/protein results |
| 10.1093/plphys/kiaa034 | KLU and leaf longevity | Joint + sequential | Abstract; RNA-seq and metabolite/hormone methods |
| 10.1097/md.0000000000047376 | Senescence genes in rheumatoid arthritis | Cross-dataset QTL/MR | 3.1-3.4 |
| 10.1111/acel.13497 | Trans-omic MR of parental lifespan | Cross-dataset QTL/MR | 2.4; 2.7; 4.2-4.6 |
| 10.1111/acel.70064 | Aged gut microbiota and cognition | Sequential + cross-layer discovery | Abstract; 2.2-2.4; 4.8-4.10 |
| 10.1111/acel.70103 | Therapeutic plasma exchange | Joint response-marker analysis | 2.4-2.5; 4.5-4.11 |
| 10.1111/acel.70328 | Photodynamic therapy and photoaging | Joint + sequential | 2.2; 3.4 |
| 10.1111/acel.70498 | Losartan metabolic rejuvenation | Parallel | 3.1-3.2 |
| 10.1126/sciadv.adu2294 | Senescent stem cells in osteoarthritis | Within-layer multiresolution + sequential | Abstract; Single-cell RNA sequencing |
| 10.1186/s12964-026-02985-y | Caspase-8 in osteoarthritis | Sequential + QTL/MR | Transcriptomic, proteomic, and MR sections |
| 10.1186/s13020-025-01154-6 | QPSM and atrial fibrillation | Joint + sequential | Transcriptomics; metabolomics; integration; western blot |
| 10.21037/tcr-2026-1-0264 | Cervical-cancer senescence model | Unclear/peripheral | Supplementary-only canonical Markdown |
| 10.2147/jir.s525168 | Senescence genes in NAFLD | Cross-dataset QTL/MR + validation | Data Sources; SMR; colocalization; validation |
| 10.26599/fshw.2026.9251125 | Cordycepin and lifespan | Joint + sequential | Abstract; Introduction aims; omics integration methods |
| 10.3389/fendo.2025.1661666 | Senescence genes in preeclampsia | Cross-dataset QTL/MR + validation | Abstract; Data sources; mQTL-eQTL analysis |
| 10.3390/microorganisms13061379 | Exercise, Akkermansia, eicosanoids | Joint microbiome-metabolome; targeted validation | Abstract; 2.4; Results/Discussion |

## Bottom line for article design

The corpus supports a main Results section on integration patterns because multi-omics plays materially different roles across the evidence base. The headline should not be the number of assays. It should be that most studies use multi-omics as a **causal workflow scaffold** rather than as a single unified model: layers nominate, localize, and triangulate, while interventions or genetic instruments provide the leverage for causal claims. A smaller set performs genuine joint integration, and paired single-cell multiome evidence remains exceptional.

For extraction and synthesis, count three things separately for every report:

1. discovery-scale normalized layers;
2. the integration operator and sample alignment;
3. the causal role of each layer, including validation-only status.

That separation will prevent targeted validation, within-layer multimodality, and external QTL proxies from being mistaken for equivalent forms of multi-omics integration.
