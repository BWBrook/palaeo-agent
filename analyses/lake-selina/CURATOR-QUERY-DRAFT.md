# Draft query to the Neotoma and IPPD curators (unsent)

Status: **draft, not sent.** Drafted by Claude (Opus 5.5) on 8 November 2026,
following Codex's [review of amendment 1](AMENDMENT-1-REVIEW.md). Sending it
is outward-facing and needs Barry's approval. Barry would send it from his
own account, to the Neotoma data stewards and the IPPD constituent-database
steward, through whatever contact route he chooses. No contact has been made.

The query asks for reconciliation. It does not claim that either the archive
or the paper is wrong, and it does not propose corrected counts.

---

**Subject:** Lake Selina (SEL1999, Neotoma dataset 52767): depth convention and one level to reconcile

Dear Neotoma and IPPD data stewards,

We have been working with the Lake Selina pollen record (Neotoma dataset
52767, collection unit SEL1999; the record lists DOIs 10.21233/5Y7N-1B24
and 10.21233/av7h-5y24), alongside its source publication: Colhoun, E.A.,
et al. (1999) *Quaternary International* 57/58: 5–23,
https://doi.org/10.1016/S1040-6182(98)00046-9. We found two discrepancies
between the archived record and the paper and would be grateful for help
reconciling them. We may be misreading the depth conventions.

**1. Depth convention of the pollen samples and the chronology controls.**

The paper (section 3, p. 8) describes a 347 cm long core with its top
assigned to 50 cm, plus a 40 cm surface core and an assumed 10 cm gap,
giving a 0–397 cm composite. The archived pollen samples span 80–427 cm,
also 347 cm.

If the archived sample depths are paper depth + 30 cm, the archived counts
reproduce nine consecutive pollen sums printed in Figure 6 exactly, when
sedge and aquatic taxa are excluded as the paper's methods describe:

| Paper depth (cm) | Archive depth (cm) | Archive sample ID | Printed sum = archive total |
| --- | --- | --- | --- |
| 70 | 100 | 531321 | 338 |
| 75 | 105 | 531323 | 335 |
| 80 | 110 | 531327 | 302 |
| 85 | 115 | 531328 | 329 |
| 90 | 120 | 531332 | 323 |
| 95 | 125 | 531330 | 344 |
| 100 | 130 | 531307 | 351 |
| 105 | 135 | 531308 | 324 |
| 110 | 140 | 531309 | 337 |

The paper's zone boundaries line up under the same shift: its herb zone
LS8 (125–170 cm) matches the archived herb maximum at 155–200 cm.

The two archived chronologies (IDs 37589 and 37590) place their radiocarbon
controls at 125, 150, 165, 230 and 295 cm, the depths printed in the paper.
If the pollen samples carry the +30 cm shift and the controls do not, each
control is attached to a level about 30 cm from the sediment that was
dated. The Bacon chronology (37590) also sets its core-top age at archive
80 cm, which under this reading would be the top of the long core at paper
50 cm rather than the sediment surface.

Could you tell us which depth convention the archived sample depths and
the chronology control depths each use, and whether any transformation was
applied to either during compilation?

**2. The level at archive 220 cm (sample 531331; paper 190 cm under the
shift above).**

The paper describes and plots a strong *Lagarostrobos* peak at 190 cm
(pp. 13 and 17). The archived level has no *Lagarostrobos* entry, and its
total under the same dryland rule is 408, against a printed sum of 480 at
that depth. We cannot tell from the published material whether this is a
compilation omission, a plotting issue in the paper, or something else.

Could you check this level against the original count sheets or the
contributor's files, if they are available?

We have not altered the archived counts. Our analysis code and these
comparisons are public at https://github.com/BWBrook/palaeo-agent (folder
`analyses/lake-selina/`), and we are happy to send anything that would help.

With thanks,

Barry Brook
University of Tasmania

---

## Notes for Barry (not part of the message)

- Page numbers are the journal's printed pages. The PDF is not attached or
  redistributed; the curators can consult the published article.
- Check the steward contacts on the Neotoma record page before sending. The
  record returns two DOIs; which version each names is unresolved.
- The message names the analysis as joint human–AI work only through the
  repository link. Add a sentence on the AI systems' roles if you want it
  stated in the message itself.
