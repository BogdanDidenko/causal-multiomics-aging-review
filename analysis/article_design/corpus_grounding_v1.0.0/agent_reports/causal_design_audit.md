# Causal-design and inferential-boundary audit

## Scope and bottom-line finding

This is an exploratory article-structure audit of the 312 Luna Light `CausalAnalysis` candidates in the 101-report corpus pack. It does not revise eligibility, PRISMA counts, or final causal levels. The graph is treated as an evidence-location index, not as adjudicated evidence.

The main finding is that `identification_status=identified` is too broad to function as a synthesis category. It often means that a manipulation and a measured contrast were present, not that a transportable causal effect of an exposure on aging was identified. The corpus is rich in controlled perturbation and mechanism testing, but most of that evidence is specific to cells, model organisms, induced disease or premature-aging models, and molecular or clock endpoints. Human intervention evidence is sparse and primarily biomarker-based. Mendelian-randomization (MR) evidence estimates effects of genetic proxies under instrument assumptions, not effects of clinical interventions. Mediation, temporal ordering, pathway enrichment, docking, and cross-omic correlation usually prioritize mechanisms rather than identify them.

A paper-level label is also inadequate. Several strong papers contain a sequence of distinct claims: omics discovery, computational prioritization, targeted perturbation, rescue or epistasis, and organismal outcomes. Each link has a different inferential boundary.

## Materials and audit method

Inputs:

- `eligible_graph_manifest_101.csv`
- `eligible_graph_profiles_101.jsonl`
- `corpus_graph_summary.json`
- the deterministic Docling Markdown linked for each report

I audited all 312 candidates quantitatively by design family, graph status, design role, report, and report-level design combination. Full-text checking covered 35 reports containing 117 candidates (37.5% of all candidates). This overlapping stratified set contained:

- all 15 `association_only`, `hypothesis_only`, or `unclear` candidates;
- all 6 formal-mediation, all 5 temporal, all 3 `other_formal_causal_design`, and the sole `dag_scm` candidate;
- 52/181 direct-perturbation candidates (28.7%);
- 17/59 nonrandomized-intervention candidates (28.8%);
- 13/24 randomized-intervention candidates (54.2%);
- 20/33 genetic-instrument candidates (60.6%).

The full-text sample was deliberately enriched for boundary cases, human interventions, rescue/epistasis designs, model-system contrasts, and papers in which the graph assigned different statuses to different steps. Conclusions below are therefore qualitative audits of likely overcalling, not a manually recoded prevalence estimate for all 297 `identified` nodes.

## Quantitative graph orientation

### Design and status labels

| Graph design family | Candidates, n (%) | Reports, n | `identified` | Other graph statuses |
|---|---:|---:|---:|---|
| Direct perturbation | 181 (58.0%) | 73 | 179 | 1 association, 1 hypothesis |
| Nonrandomized intervention | 59 (18.9%) | 40 | 59 | 0 |
| Genetic instrument | 33 (10.6%) | 14 | 30 | 1 association, 1 hypothesis, 1 unclear |
| Randomized intervention | 24 (7.7%) | 18 | 22 | 2 association |
| Formal mediation | 6 (1.9%) | 5 | 2 | 1 association, 3 hypothesis |
| Temporal identification | 5 (1.6%) | 4 | 4 | 1 association |
| Other formal causal design | 3 (1.0%) | 3 | 1 | 2 association |
| DAG/SCM | 1 (0.3%) | 1 | 0 | 1 hypothesis |
| **Total** | **312** | **100 with nodes** | **297** | **15** |

Thus, 95.2% of candidates are graph-labeled `identified`; only 2.6% are `association_only`, 1.9% `hypothesis_only`, and 0.3% `unclear`. The dominant design labels are experimental: direct perturbation plus randomized or nonrandomized intervention account for 264/312 candidates (84.6%). At report level, direct perturbation appears in 73/101 reports and nonrandomized intervention in 40/101.

Graph design roles are similarly identification-heavy: 187/312 (59.9%) are `primary_identification`, 113 (36.2%) `supporting_identification`, 11 (3.5%) `validation_only`, and 1 (0.3%) `mentioned_only`.

### Candidate fragmentation

The 312 nodes are not 312 independent studies or effects. Reports contain 0-9 candidates (median 3; mean 3.09). Twenty-one reports have one candidate, while 59 have three or more. Direct perturbation alone contributes 181 nodes from 73 reports. A single mechanistic chain can generate separate nodes for knockout, overexpression, inhibitor, rescue, binding, and downstream validation. Results should therefore use report and claim-chain units, not raw node counts, for substantive synthesis.

The most common report-level signatures reinforce this point:

- direct perturbation plus nonrandomized intervention: 28 reports;
- direct perturbation only: 26;
- genetic instrument only: 10;
- direct perturbation plus randomized intervention: 8;
- randomized intervention only: 7;
- nonrandomized intervention only: 5.

### Composite-document leakage

Six proceedings or conference-abstract records contribute 25 graph candidates: five `10.1093/geroni/...` records and `10.4081/ejtm.2026.14960`. Full-text section matching shows that at least 17/25 candidates are taken from adjacent abstracts rather than the abstract named in the manifest title.

Examples:

- **OXR1 STABILIZES THE RETROMER...** (`10.1093/geroni/igac059.2661`) has valid focal evidence for the OXR1 GWAS, neuronal knockdown, and retromer rescue. Four other nodes come from neighboring abstracts on senolytics/alpha-Klotho and Scl-mAb/Dkk1-mAb bone therapy.
- **BIOLOGICAL AGE REDUCTION...** (`10.1093/geroni/igad104.1942`) contains the focal heterochronic-parabiosis result, but its Look AHEAD node belongs to abstract `igad104.1941`.
- **MULTIMODEL APPROACHES...** (`10.1093/geroni/igae098.2630`) contains the focal IDO1/IDO2 knockout abstract, while its treadmill node is from `igae098.2631`.
- `10.4081/ejtm.2026.14960` is titled as Abstract 009, but all eight graph nodes are anchored to Abstracts 038, 040, 052, 054, 055, 065, and 068.

These nodes can point to real evidence in the source file, but they cannot be attributed to the manifest-titled report. They should be excluded from title-level examples unless the proceedings are deliberately analyzed as a multi-abstract container.

## Audit of every weak-status candidate

The 15 weak candidates occur in 12 reports. In general, their weak graph status is more defensible than the blanket `identified` status assigned elsewhere.

| DOI and title | Weak candidate(s) | Full-text assessment |
|---|---|---|
| `10.1038/s41392-026-02799-x`, **Multiomic profiling of responses to clinical and novel bisphosphonates...** | RCT literature summary, `association_only` | In Results, **Bisphosphonate treatment is associated with reduced disease progression and severity**, the paper descriptively summarizes heterogeneous prior trials and non-bone events. It does not estimate a new pooled extraskeletal effect. The same paper does support treatment effects on proteomic, murine, and cell endpoints, but not the broad mortality narrative. |
| `10.1038/s41467-023-37729-w`, **Multi-omic underpinnings of epigenetic aging and human longevity** | TWAS/FOCUS, `hypothesis_only` | Appropriate. The Discussion explicitly characterizes the study as hypothesis-generating and calls for in vitro and in vivo validation. Even the MR-positive target screens remain assumption-limited; the paper notes imperfect control of LD and pleiotropy, possible false positives, sample overlap, and European-ancestry restriction. |
| `10.1038/s41586-026-10524-5`, **Sleep chart of biological ageing clocks in middle and late life** | SEM `association_only`; MR `unclear`; Cox model `association_only` | Appropriate. Methods say the SEM is not strict causal inference; the MR tests disease -> sleep because the reverse direction lacked power; pleiotropy-robust methods did not corroborate the MDD signal; and Limitations call the principal design cross-sectional with residual confounding and reverse causation. The Cox analysis gives temporal association with mortality, not exchangeability. |
| `10.1093/bib/bbag271`, **StackAge...** | SEM mediation, `hypothesis_only` | Appropriate. The **Mediation analysis** section uses a Sobel test and a relaxed `P < .1`; omics are cross-sectional, and socioeconomic status, medication, and comorbidity are omitted. Limitations explicitly call for future causal modeling. |
| `10.1093/eurheartj/ehad361`, **Subclinical atherosclerosis and accelerated epigenetic age mediated by inflammation** | Two model-based mediation nodes, both `hypothesis_only` | Appropriate. The **Mediation analysis** section invokes sequential ignorability based mainly on age/sex matching, acknowledges unknown directionality, and says the reverse model is harder to justify. Results call 114 genes *potential* mediators. This is useful pathway decomposition, not established mediation. |
| `10.1093/geroni/igaa057.414`, **Metabolic Regulation of Longevity by One-Carbon Metabolism...** | Medifast trial node, `association_only` | Appropriate and off-title. In the neighboring **Nicotinamide and sugar metabolism...** abstract, 38 metabolomics participants from the treatment arm are analyzed by change-change correlation. Randomization into the parent trial does not identify metabolites as mediators of lean-mass change. |
| `10.1093/geroni/igac059.2661`, **OXR1 stabilizes the retromer...** | GWAS, `association_only` | Appropriate for the discovery step. The focal abstract then moves beyond association: neuronal `mtd/OXR1` knockdown impairs lifespan/neuronal health and retromer overexpression or R55 rescues the defect. The paper's mechanism is supported by perturbation, not by the GWAS alone. |
| `10.1186/s12964-026-02985-y`, **Multi-omics and experimental evidence...caspase-8...** | In silico knockout, `hypothesis_only` | Appropriate. The in silico perturbation is a sensitivity analysis. The stronger evidence is pharmacologic inhibition in primary chondrocytes and MR/SMR. Importantly, the **Modification of caspase-8 catalytic activity...** section reports that CASP8 siRNA achieved 85% knockdown but did not change senescence, proliferation, viability, or apoptosis, weakening a simple target-specific interpretation of the inhibitor result. |
| `10.1186/s40364-023-00458-9`, **The essential roles of FXR...** | Spearman correlation, `association_only` | Appropriate. Cross-omic transcript-metabolite-microbiome correlations do not identify direction. WT/FXR-knockout and diet contrasts do support genotype- and diet-specific effects, while the Discussion says new molecular roles require phenotypic validation in other models. |
| `10.21203/rs.3.rs-1264931/v1`, **Multi-omics analysis reveals a non-canonical regulatory pattern of UPL3...** | Pulldown-MS interaction, `association_only` | Appropriate. Knockout, overexpression, and complementation support an effect of UPL3 on Arabidopsis leaf senescence. Pulldown-MS plus yeast two-hybrid supports physical interaction, but not the full direction of a UPL3-UBP12/BRM/PPC2 causal chain; the paper itself notes unresolved direct ubiquitination and inconsistent PPC2 behavior. |
| `10.26599/fshw.2026.9251125`, **Unraveling the Key Pathways through Cordycepin...** | Network pharmacology/docking, `hypothesis_only` | Appropriate. Section **3.6.1 Anti-aging target prediction and molecular docking analysis** explicitly says docking is hypothesis-generating and does not establish binding. Treatment extends worm lifespan and `daf-16` loss abolishes the benefit, supporting DAF-16 dependence; direct cordycepin -> DAF-2/IGF-1R engagement remains untested. |
| `10.3892/or.2026.9080`, **NR4A1 mediates chemotherapy-induced senescence...** | GEPIA2 survival, `association_only` | Appropriate. The clinical survival curve is observational and directionally complicated: Discussion contrasts acute pro-senescence effects in cells with poor prognosis at high tumor NR4A1. The shRNA experiment supports an NR4A1 role in oxaliplatin-induced senescence in two gastric-cancer cell lines, not a clinical survival effect. |

## Recurring causal logics actually present

### 1. Omics discovery followed by targeted perturbation

This is the dominant and most article-defining logic. Omics nominate a target or pathway; genetic or pharmacologic manipulation then tests a specific link. Strong examples use both directions or a rescue/epistasis step:

- **ATF3 Deficiency Exacerbates Ageing-Induced Atherosclerosis...** (`10.1002/advs.202502249`): single-cell discovery is followed by smooth-muscle ATF3 loss, ATG7 perturbation, terazosin treatment, and loss of terazosin benefit after ATF3 silencing. Sections **2.6 Silencing ATF3 in VSMCs Abolishes the Anti-Ageing Effects of TZ** and **2.8 TZ Improves AS...** support ATF3-dependent efficacy in SAMP8 and ApoE-knockout mice. This identifies a mechanism in those models, not clinical efficacy; the Discussion says larger RCTs are needed.
- **Targeting KAT8 Alleviates Vascular Senescence...** (`10.1016/j.ymthe.2025.12.035`): CRISPR loss and activation produce opposite senescence phenotypes; animal overexpression/knockdown extends the contrast; INHBA siRNA impairs KAT8 rescue. This is mechanistic necessity/rescue, even though the graph calls the final node `formal_mediation`.
- **Microbiota-derived indole acetic acid extends lifespan...** (`10.1128/msystems.01665-24`): IAA extends lifespan in wild-type flies, not `Ahr` mutants; `Sirt2` RNAi and mutation also abolish extension; ChIP and reporter assays connect AhR to the `Sirt2` promoter. This supports pathway dependence in Drosophila, not mammalian geroprotection.
- **Reducing the metabolic burden of rRNA synthesis...** (`10.1038/s41467-024-46037-w`): `tif-1A`/`rpoa-2` knockdown extends worm lifespan, `tif-1A` overexpression and `ncl-1` knockdown move pre-rRNA and lifespan in the opposite direction, and `atgl-1` co-inactivation tests the lipid mechanism. Human fibroblast drug experiments only validate a cellular metabolic-stress response.
- **Multiomic single-cell perturbation screens...** (`10.1038/s43587-026-01100-7`): Perturb-seq is itself a causal screen within K562 cells; HOTAIRM1 siRNA and overexpression test DNA-repair/senescence phenotypes; AAV overexpression tests aged mouse lung injury. Bleomycin-induced temporal expression is supporting context, not a separate identification design.

This recurring logic warrants a Results section organized as **discovery -> perturbation -> rescue/epistasis -> endpoint -> system boundary**.

### 2. Whole-system interventions with omics as downstream readouts

Animal diet, drug, exercise, transplantation, FMT, parabiosis, and induced-injury studies are common. Many graph `nonrandomized_intervention` nodes are ordinary controlled laboratory experiments, not quasi-experiments in the epidemiologic sense. Conversely, `randomized_intervention` frequently means animal group assignment. Only 5/24 randomized nodes have human-participant populations; two are graph-labeled association-only and one belongs to an adjacent conference abstract.

Representative stronger contrasts include:

- **Aged Gut Microbiota Contributes to Cognitive Impairment...** (`10.1111/acel.70064`): aged-donor FMT transfers cognitive and synaptic phenotypes to young mice; B. pseudolongum/IAA supplementation and AHR blockade refine the mechanism. The multicomponent FMT effect is causal in recipient mice; the human abundance-cognition result remains associational.
- **Multi-omic rejuvenation and lifespan extension upon exposure to youthful circulation** (`10.1038/s43587-023-00451-9`): long-term heterochronic versus isochronic parabiosis followed by detachment changes lifespan, function, clocks, and liver/blood omics in old female mice. Methods include randomized pair selection and post-detachment blinding. The effect is of the full parabiosis procedure/shared circulation, not an identified circulating factor.
- **Midkine as a driver of age-related changes...** (`10.1016/j.ccell.2024.09.002`): exogenous midkine increases mammary epithelial proliferation and NMU tumorigenesis in randomized rat groups; SREBF1/mTOR inhibitors block organoid proliferation. Because the study did not inhibit endogenous midkine in aging animals, it establishes sufficiency of administered midkine more clearly than necessity of endogenous midkine.

### 3. Human assigned interventions identify biomarker effects, not general rejuvenation

- **Therapeutic plasma exchange** (`10.1111/acel.70103`) is a single-blind randomized sham-controlled study with 42 completers. It supports effects on selected epigenetic-clock contrasts at an intermediate time point. However, most clocks differed at baseline; no within-group clock survived FDR correction; no functional, cognitive, symptomatic, morbidity, or mortality outcomes were assessed; and no group remained significantly different from sham at the final time point. The allowable claim is that TPE regimens changed clock estimates in this small trial, not that TPE rejuvenated participants.
- **Losartan** (`10.1111/acel.70498`) reanalyzes a phase II placebo-controlled trial in only 16 pre-frail men (placebo n=9, losartan n=7). Section **3.4 Losartan Dose-Dependently Opposes Serum Metabolomic Aging Signature...** reports a molecular-signature shift, but the dose-escalation design confounds dose with time. The mouse survival arm had 33 males, two months of follow-up, and no complete lifespan curve. Both are signals for further testing, not definitive rejuvenation or longevity effects.
- The Look AHEAD abstract (`10.1093/geroni/igad104.1942` container, actual abstract `igad104.1941`) reports an unexpected increase in one of five clocks, null effects on four other clocks, and no frailty-index change in 62 women after 14 years. Randomization identifies the long-term intervention contrast in that subset, but not a coherent anti-aging effect.

### 4. Genetic instruments estimate lifelong proxy effects

The best MR papers explicitly define instruments, assess direction, pleiotropy and heterogeneity, and use colocalization or replication. Even then, the estimand is a genetically proxied, usually lifelong exposure in the represented ancestry and tissue context.

- **Major Psychiatric Disorders, Substance Use Behaviors, and Longevity** (`10.1001/jamapsychiatry.2024.1429`) is a stronger example. **MR Assumptions** and **Statistical Analysis** specify relevance, exclusion restriction, pleiotropy checks, MRLap for overlap, Steiger directionality, negative controls, MVMR, a CHRNA5-CHRNA3-CHRNB4 instrument, and replication. It supports a genetic-liability estimate for lifetime smoking in European-ancestry data. It does not estimate the effect of smoking cessation or a protein-targeting drug on lifespan.
- **A trans-omic MR study of parental lifespan...** (`10.1111/acel.13497`) uses TWAS, colocalization, cis instruments, MR-PRESSO, MR-Egger, and contamination-mixture models. The paper still states that results lack independent-cohort validation and require prospective trials. Tissue-specific opposite directions at some loci and parental lifespan as a proxy constrain target claims.
- **Multi-omics data reveal causal associations...rheumatoid arthritis** (`10.1097/md.0000000000047376`) is a boundary example. In Limitations, the authors state that eQTL/pQTL findings lack external validation, are weak and susceptible to weak-instrument bias, and mainly support mQTL signals; only NEK4 had strong reported mQTL-RA colocalization among the highlighted loci. Blood QTLs may not represent synovium. The graph's broad `identified` wording exceeds the paper's own boundary.
- **Depletion of loss-of-function germline mutations in centenarians...** (`10.1038/s41467-024-52967-2`) combines rare-variant burden evidence with common cis-eQTL MR. Its Limitations call for functional validation. Consistency across aging traits prioritizes RGP1, PCNX2, and ANO9, but does not by itself prove that changing their expression will extend lifespan.

### 5. Statistical direction and temporal ordering are usually support, not identification

- In **Multiomic profiling of the liver across diets and age...** (`10.1016/j.cels.2021.09.005`), stabilized regression uses genotype, diet, and age environments to classify associations as statistically upstream, downstream, or ambiguous. The Results explicitly note that some robust associations cannot be directionally resolved. Separate C. elegans RNAi experiments establish effects of `asp-4/Ctsd` and `st-7` on lifespan. The graph should not merge the statistical upstream classification with the perturbational effect.
- In **Metabolic reprogramming during hyperammonemia...** (`10.1172/jci.insight.154089`), ammonia treatment, withdrawal, rechallenge, and ammonia lowering are controlled perturbations. The rechallenge supports history-dependent response in myotubes, but Discussion notes medium replacement, unknown mechanisms, and the need for in vivo recurrence studies. It is not a general longitudinal identification design.
- In **A uterine-centric view of reproductive senescence...** (`10.1002/imo2.70128`), the paper carefully calls uterus weight a *statistically supported intermediate phenotype*. SNP, uterus weight, and late-life traits are analyzed in 254 hens at 100 weeks; ACME/ADE decomposition does not itself establish manipulable mediation. The graph's statement that variants increase egg production *through* uterus weight is stronger than the evidence warrants.

## Where `identified` is unjustified or only system-specific

1. **A manipulated contrast can be identified while the aging claim is not.** Oxaliplatin causes senescence markers in gastric-cancer cells (`10.3892/or.2026.9080`), MPTR changes clocks and migration in selected fibroblasts (`10.7554/elife.71624`), and mTOR inhibitors change progeria iPSC-VSMC markers (`10.1093/geroni/igaf122.3850`). These are causal effects on those endpoints and systems, not demonstrated effects on organismal aging.

2. **Premature-aging and disease models delimit transport.** Muscle-specific Bmal1 restoration improves survival in a global Bmal1-knockout mouse (`10.1172/jci.insight.174007`, section **Skeletal muscle-specific expression of Bmal1 increases the lifespan...**), but that model has severe clock deficiency and a roughly 37-week median lifespan. The result establishes rescue in that genotype, not normal-aging lifespan extension.

3. **Biomarker reversal is not equivalent to rejuvenation.** Clock, transcriptomic-age, metabolomic-age, pathway, or cell-composition changes can be legitimate treatment effects. Calling them biological rejuvenation requires validation that the marker change tracks improved function, morbidity, or survival under intervention rather than treatment-sensitive composition or assay shifts.

4. **Pathway enrichment after treatment does not identify mediation.** A treatment can cause both an omics change and a phenotype without the omics feature causing the phenotype. Necessity, sufficiency, rescue, or intervention-on-mediator evidence is needed for a mechanistic link.

5. **Target engagement and pathway dependence are distinct.** Cordycepin requires DAF-16 in worms, but docking does not establish direct DAF-2 binding. UPL3 affects plant senescence, but pulldown does not establish the full direction of its partner network. Caspase-8 inhibitor effects are not resolved by a null siRNA phenotype.

6. **MR identification is conditional and proxy-specific.** Instrument strength, independence, exclusion restriction, colocalization, tissue, ancestry, sample overlap, and time-varying exposure all bound the claim. Drug-target and cessation effects are downstream hypotheses unless directly tested.

7. **Conference-container attribution can be wrong even when the excerpt is real.** At least 17 candidates are not evidence for their manifest titles. This is a document-segmentation problem, not a causal judgment.

## Recommended six-category causal taxonomy

The taxonomy should be applied at the claim/link level. A report may occupy several categories.

| Category | What it supports | Minimum evidence and boundary | Preferred Results language | Representative / boundary examples |
|---|---|---|---|---|
| **1. Assigned intervention effect** | Effect of an assigned or controlled exposure on a prespecified measured endpoint in the studied system | Clear comparator, assignment process, timing, and endpoint; randomization/blinding where applicable. Does not establish mechanism or transport. | "Treatment X changed Y in population/model Z." | TPE `10.1111/acel.70103`; parabiosis `10.1038/s43587-023-00451-9`; losartan boundary `10.1111/acel.70498`. |
| **2. Perturbational mechanism: necessity, sufficiency, or rescue** | Whether a target/pathway component contributes to an effect in a defined system | Targeted loss/gain, inhibitor with specificity controls, epistasis, or rescue. State which logical property was tested; avoid general causal claims from a single direction. | "X was required for...", "X was sufficient to...", or "rescue of X restored...in Z." | ATF3 `10.1002/advs.202502249`; KAT8/INHBA `10.1016/j.ymthe.2025.12.035`; IAA-AhR-Sirt2 `10.1128/msystems.01665-24`; Bmal1 boundary `10.1172/jci.insight.174007`. |
| **3. Post-intervention omics response** | Causal effect of an intervention on a molecular profile, clock, inferred cell composition, or pathway score | Valid intervention contrast and molecular endpoint. The response is downstream evidence, not automatically a mediator or aging reversal. | "X shifted the Y signature" or "Y changed after X"; avoid "rejuvenated" without functional validation. | Bisphosphonate `10.1038/s41392-026-02799-x`; MPTR `10.7554/elife.71624`; TPE and losartan boundaries above. |
| **4. Genetic-proxy causal inference** | Effect of a genetically proxied exposure, molecular trait, or liability under IV assumptions | Relevance, direction, exclusion/pleiotropy assessment, multiplicity control, colocalization where appropriate, and tissue/ancestry definition. Not equivalent to a drug or behavioral intervention. | "Genetically proxied X was estimated to affect Y under MR assumptions." | Smoking-longevity `10.1001/jamapsychiatry.2024.1429`; parental lifespan `10.1111/acel.13497`; RA boundary `10.1097/md.0000000000047376`. |
| **5. Temporal or statistical path evidence** | Temporal sequence, indirect-effect decomposition, or statistically upstream/downstream organization | Longitudinal or mediation model plus explicit exchangeability/temporal assumptions. Without them, supports ordering or consistency, not identification. | "X preceded Y", "the indirect association was consistent with...", or "X was statistically upstream." | PESA `10.1093/eurheartj/ehad361`; StackAge `10.1093/bib/bbag271`; stabilized regression `10.1016/j.cels.2021.09.005`. |
| **6. Associational or computational prioritization** | Candidate target, pathway, interaction, or direction for testing | Correlation, survival association, enrichment, network pharmacology, docking, TWAS without adequate causal support, or in silico perturbation. | "associated with", "prioritized", "predicted", or "hypothesis-generating". | Cordycepin docking `10.26599/fshw.2026.9251125`; UPL3 pulldown `10.21203/rs.3.rs-1264931/v1`; NR4A1 survival `10.3892/or.2026.9080`. |

## Recommended Results architecture

### Results 1: Corpus map and unit of evidence

Report the graph distributions as an orientation signal, clearly labeled model-generated. Show candidates and reports side by side. State that 297/312 `identified` labels were not accepted as causal judgments. Include candidate fragmentation and the composite-document leakage audit. Do not turn graph counts into review findings or update eligibility/PRISMA/final causal levels.

### Results 2: From omics discovery to perturbational mechanism

Organize multi-step papers as causal chains rather than as lists of omics layers:

`discovery -> target selection -> loss/gain perturbation -> rescue/epistasis -> organismal endpoint`

For each chain, identify the strongest tested link and its system. Separate necessity, sufficiency, rescue, binding, and downstream response. ATF3, KAT8/INHBA, rRNA/Pol I, HOTAIRM1, IAA-AhR-Sirt2, OXR1-retromer, and cordycepin-DAF-16 are representative; cordycepin-DAF-2 binding, UPL3 partner direction, and CASP8 inhibitor specificity are useful boundaries.

### Results 3: Intervention effects, ordered by endpoint and transportability

Separate human randomized evidence, controlled animal interventions, cellular interventions, and induced-aging/disease models. Within each, order outcomes:

1. lifespan, morbidity, or validated function;
2. tissue/pathology phenotype;
3. molecular aging clock or omics signature;
4. pathway enrichment or inferred composition.

This prevents clock movement from being presented beside lifespan as equivalent rejuvenation. Randomization should be reported as a design feature, not a category that automatically confers mechanistic identification.

### Results 4: Genetic-proxy evidence

Give MR/SMR a dedicated section because its estimands and assumptions differ from perturbation experiments. For each representative claim, report exposure proxy, outcome, ancestry/tissue, number/type of instruments, colocalization, pleiotropy/heterogeneity tests, replication, and the intervention that the estimate does *not* identify.

### Results 5: Mediation, temporal, and hypothesis-generating evidence

Group mediation, Cox models, stabilized regression, correlation, docking, network pharmacology, and in silico perturbation as supporting causal architecture rather than as equivalent effect identification. Present them as links that motivate or contextualize perturbation. Preserve explicit author caveats such as "potential mediator," "not strict causal inference," and "direct binding remains to be established."

### Results 6: Inferential boundaries across systems

End Results with a compact evidence-gap matrix: human versus animal/cell/plant; normal aging versus induced disease/premature aging; lifespan/function versus molecular proxies; discovery-only versus perturbation/rescue; and focal report versus composite-document evidence. The corpus-level conclusion should be:

> The literature is perturbation-rich and frequently mechanism-oriented, but its strongest causal claims are usually local to experimental systems. Human evidence mainly identifies effects on molecular proxies, while genetic-instrument studies provide conditional lifelong-proxy estimates. Translation from pathway perturbation or clock change to improved human healthspan remains the central gap.

## Practical claim-auditing rules for article drafting

1. Use the claim/link, not the paper, as the unit of causal classification.
2. Always name the system and endpoint in the same sentence as the causal verb.
3. Reserve "mediates" for intervention-on-mediator, valid mediation identification, or strong rescue/epistasis; otherwise use "is consistent with" or "is a candidate pathway."
4. Reserve "rejuvenation" for convergent functional evidence; use "younger-shifted molecular signature" for clocks or omics alone.
5. For MR, say "genetically proxied" and state the ancestry/tissue and core diagnostics.
6. Do not infer a direct molecular target from docking, enrichment, colocalization, or pathway dependence.
7. Separate assigned-treatment effects from post-treatment mechanism narratives.
8. Exclude off-title proceedings candidates from report-level examples unless the adjacent abstract is separately named and cited.

## Limitations of this audit

- The 312 candidates are model-generated and may omit or fragment evidence.
- Full-text validation was stratified and boundary-enriched, not a random sample. It supports an inferential audit but not an exact corrected prevalence of causal categories.
- Deterministic Docling Markdown was used; figures and supplements were considered only when described in the Markdown.
- No eligibility decision, PRISMA count, or final causal level was reassessed.

## Conclusion

The graph correctly reveals that the corpus is dominated by perturbational work, but `identified` collapses at least four different meanings: an assigned treatment effect, a system-specific mechanism test, a post-intervention molecular response, and a genetic-proxy estimate. It also misclassifies several statistical or computational methods and can leak evidence across adjacent conference abstracts. The article should therefore be structured around the six claim-level causal logics above, with endpoint, system, assumptions, and transport boundary made explicit. This preserves the real strength of the corpus, namely omics-guided experimental mechanism testing, without converting local perturbations, molecular signatures, or narrated direction into general causal effects on human aging.
