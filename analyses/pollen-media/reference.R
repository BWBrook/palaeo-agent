# Independent arithmetic/input check under primer section 7; API results remain the reported results.
# Rscript --vanilla analyses/pollen-media/reference.R /path/to/pinned-iNEXT-source-directory
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L)
script <- normalizePath(sub("^--file=", "", commandArgs()[grepl("^--file=", commandArgs())]))
here <- dirname(script)
root <- normalizePath(file.path(here, "../.."))
libraries <- list.dirs(file.path(root, "references/r/renv/library"), recursive = TRUE)
libraries <- libraries[basename(libraries) == R.version$platform & dir.exists(file.path(libraries, "vegan"))]
.libPaths(c(libraries, .libPaths()))
stopifnot(requireNamespace("vegan", quietly = TRUE), requireNamespace("jsonlite", quietly = TRUE))
sha256 <- function(path) strsplit(system2("shasum", c("-a", "256", shQuote(path)), stdout = TRUE), " ")[[1L]][1L]
read_json <- function(path) jsonlite::fromJSON(path, simplifyVector = FALSE)
vec <- function(x) unlist(x, use.names = FALSE)
mat <- function(x) do.call(rbind, lapply(x, vec))
inext <- file.path(normalizePath(args[[1L]]), "iNEXT.r")
stopifnot(sha256(inext) == "ebda76c6f9477c44141900314e94aa0a20498be015afe21877d6d26f170f7619")
env <- new.env(parent = baseenv())
assignment <- Filter(function(e) is.call(e) && as.character(e[[1L]]) %in% c("<-", "=") &&
                       identical(e[[2L]], as.name("Chat.Ind")), as.list(parse(inext)))
stopifnot(length(assignment) == 1L)
eval(assignment[[1L]], envir = env)

checks <- list()
check <- function(name, api, reference, relative = 1e-10, absolute = 1e-12) {
  a <- as.numeric(vec(api)); b <- as.numeric(vec(reference))
  stopifnot(length(a) == length(b), length(a) > 0L, all(is.finite(a)), all(is.finite(b)))
  error <- abs(a - b); passed <- error <= pmax(absolute, relative * abs(b))
  checks[[name]] <<- list(n_fields = length(a), n_agree = sum(passed), max_abs_difference = max(error),
                         relative_tolerance = relative, absolute_tolerance = absolute,
                         disagreements = if (all(passed)) list() else lapply(which(!passed), function(i)
                           list(index = i, api = a[i], reference = b[i], difference = error[i])))
}
exact <- function(name, api, reference) {
  a <- as.character(vec(api)); b <- as.character(vec(reference))
  stopifnot(length(a) == length(b))
  checks[[name]] <<- list(n_fields = length(a), n_agree = sum(a == b), max_abs_difference = 0,
                         exact = TRUE, disagreements = if (identical(a, b)) list() else
                           lapply(which(a != b), function(i) list(index = i, api = a[i], reference = b[i])))
}

ids <- c("1466027", "1466028", "1466029", "1480879", "1480880", "1480881", "1480882")
excluded <- c("Cyperaceae", "Restionaceae", "Gymnoschoenus")
trap <- list(c("1466029", "1466027"), c("1466029", "1466028"), c("1480879", "1480880"),
             c("1480879", "1480881"), c("1480879", "1480882"))
baseline <- list(c("1480880", "1480881"), c("1480880", "1480882"), c("1480881", "1480882"))
source_path <- file.path(root, "analyses/tas-surface/source/neotoma-tas-surface-download.json")
stopifnot(sha256(source_path) == "0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36")
source <- read_json(source_path)
records <- Filter(function(x) x$site$collectionunit$dataset$datasetid %in% c(74305, 74913), source$data)
samples <- do.call(c, lapply(records, function(x) x$site$collectionunit$dataset$samples))
kept <- lapply(samples, function(s) Filter(function(d) d$element %in% c("pollen", "pollen/spore", "spore") &&
                                           d$ecologicalgroup %in% c("TRSH", "UPHE"), s$datum))
labels <- sort(unique(vec(lapply(kept, function(ds) vapply(ds, function(d) d$variablename, "")))), method = "radix")
source_ids <- vapply(samples, function(s) as.character(s$sampleid), "")
x <- matrix(0, length(source_ids), length(labels), dimnames = list(source_ids, labels))
for (i in seq_along(kept)) for (datum in kept[[i]]) {
  stopifnot(datum$units == "NISP", datum$value >= 0, datum$value == floor(datum$value))
  x[i, datum$variablename] <- datum$value
}
input <- file.path(here, "data/counts.tsv")
table <- as.matrix(read.delim(input, row.names = 1L, check.names = FALSE))
exact("input/sample_source_order", rownames(table), source_ids)
exact("input/taxon_order", colnames(table), labels)
check("input/source_count_cells", table, x, relative = 0, absolute = 0)
stopifnot(all(excluded %in% labels), length(ids) == 7L, length(labels) == 82L)
inclusive <- x[ids, , drop = FALSE]
primary <- inclusive[, !colnames(inclusive) %in% excluded, drop = FALSE]
metadata <- read.csv(file.path(here, "data/samples.csv"), colClasses = "character", check.names = FALSE)
exact("metadata/sample_order", metadata$sample_id, ids)
exact("metadata/sites", metadata$site, c(rep("Hartz Mountains", 3), rep("Tyndall Ranges", 4)))
exact("metadata/archived_indices", metadata$archived_index, c(1, 2, 3, 1, 2, 3, 4))
exact("metadata/media", metadata$medium, c("core top", "moss polster", "pollen trap", "pollen trap", rep("surface sample", 3)))
study <- read_json(file.path(here, "study.json"))
exact("study/primary_selection", study$datasets$primary$operations[[1L]]$samples, ids)
exact("study/primary_exclusions", study$datasets$primary$operations[[2L]]$taxa, excluded)
exact("study/inclusive_selection", study$datasets$inclusive$operations[[1L]]$samples, ids)
stopifnot(length(study$datasets$primary$operations) == 2L, length(study$datasets$inclusive$operations) == 1L)
r <- read_json(file.path(here, "results.json"))
exact("run/status", c(r$study_status, r$inspection_status), c("complete", "verified"))

for (name in c("primary", "inclusive")) {
  z <- if (name == "primary") primary else inclusive
  api <- r[[paste0(name, "_community")]]
  exact(paste0(name, "/sample_ids"), api$sample_ids, ids)
  exact(paste0(name, "/taxon_ids"), api$taxon_ids, colnames(z))
  exact(paste0(name, "/community_settings"), c(api$value_type, api$transform, api$distance, api$dimensions),
        c("count", "relative_abundance", "braycurtis", 2))
  d <- api$diversity
  check(paste0(name, "/totals"), lapply(d, function(s) s$total), rowSums(z), 0, 0)
  check(paste0(name, "/richness"), lapply(d, function(s) s$richness), vegan::specnumber(z), 0, 0)
  check(paste0(name, "/shannon"), lapply(d, function(s) s$shannon), vegan::diversity(z, "shannon"))
  check(paste0(name, "/simpson"), lapply(d, function(s) s$simpson), vegan::diversity(z, "simpson"))
  dist <- as.matrix(vegan::vegdist(vegan::decostand(z, "total"), "bray"))
  check(paste0(name, "/relative_braycurtis_matrix"), mat(api$distances), dist, 0, 1e-12)
}

rare <- r$primary_rarefaction
m <- vec(rare$sizes)
stopifnot(length(m) == 1L)
check("rarefaction/common_size", m, min(rowSums(primary)), 0, 0)
reference_warnings <- list()
rare_ref <- lapply(seq_len(nrow(primary)), function(i) {
  z <- primary[i, ]
  value <- as.numeric(withCallingHandlers(vegan::rarefy(z, sample = m, se = TRUE), warning = function(w) {
    reference_warnings[[rownames(primary)[i]]] <<- conditionMessage(w)
    invokeRestart("muffleWarning")
  }))
  c(total = sum(z), observed_richness = vegan::specnumber(z), f1 = sum(z == 1), f2 = sum(z == 2),
    full_coverage = env$Chat.Ind(z, sum(z)), expected_richness = value[1L], conditional_sd = value[2L],
    variance = value[2L]^2, coverage = env$Chat.Ind(z, m))
})
exact("rarefaction/sample_ids", lapply(rare$samples, function(s) s$sample_id), ids)
for (field in c("total", "observed_richness", "f1", "f2", "full_coverage", "expected_richness", "conditional_sd", "variance", "coverage")) {
  api <- lapply(rare$samples, function(s) if (field %in% c("total", "observed_richness", "f1", "f2", "full_coverage")) s[[field]] else s$estimates[[1L]][[field]])
  check(paste0("rarefaction/", field), api, lapply(rare_ref, function(s) s[[field]]))
}

families <- list()
for (name in c("trap_primary", "trap_inclusive", "baseline_tyndall_surface")) {
  api <- r[[name]]; z <- if (name == "trap_inclusive") inclusive else primary
  wanted <- if (name == "baseline_tyndall_surface") baseline else trap
  exact(paste0(name, "/pairs_and_order"), lapply(api$pairs, function(p) p$sample_ids), wanted)
  check(paste0(name, "/retained_counts"), mat(api$retained_counts), z, 0, 0)
  exact(paste0(name, "/randomization"), c(api$randomization$simulations, api$randomization$seed), c(99999, 20261108))
  exact(paste0(name, "/family_sizes"), c(api$multiplicity$omnibus$size, api$multiplicity$joint_control), c(length(wanted), FALSE))
  fisher_api <- fisher_ref <- holm_api <- effect_api <- effect_ref <- numeric()
  cp <- matrix(NA_real_, length(wanted), 2)
  plusone <- numeric(length(wanted))
  distances <- as.matrix(vegan::vegdist(vegan::decostand(z, "total"), "bray"))
  for (i in seq_along(wanted)) {
    p <- api$pairs[[i]]; a <- z[wanted[[i]][1L], ]; b <- z[wanted[[i]][2L], ]; present <- a + b > 0
    exact(paste0(name, "/pair", i, "_taxa"), lapply(p$taxon_tests, function(t) t$taxon_id), colnames(z)[present])
    tests <- vapply(which(present), function(j) stats::fisher.test(matrix(c(a[j], sum(a)-a[j], b[j], sum(b)-b[j]), nrow = 2L, byrow = TRUE), alternative = "two.sided")$p.value, 0)
    fisher_api <- c(fisher_api, vec(lapply(p$taxon_tests, function(t) t$p_value)))
    fisher_ref <- c(fisher_ref, tests)
    holm_api <- c(holm_api, vec(lapply(p$taxon_tests, function(t) t$p_value_holm)))
    effect_api <- c(effect_api, vec(lapply(p$taxon_tests, function(t) t$proportion_difference_b_minus_a)))
    effect_ref <- c(effect_ref, (b/sum(b)-a/sum(a))[present])
    chi <- suppressWarnings(stats::chisq.test(rbind(a[present], b[present]), correct = FALSE))
    check(paste0(name, "/pair", i, "_braycurtis"), p$braycurtis_proportions, distances[wanted[[i]][1L], wanted[[i]][2L]])
    check(paste0(name, "/pair", i, "_pearson"), p$pearson_chi_squared, unname(chi$statistic))
    check(paste0(name, "/pair", i, "_sample_totals"), p$sample_totals, c(sum(a), sum(b)), 0, 0)
    B <- p$monte_carlo$simulations; k <- p$monte_carlo$count_extreme
    plusone[i] <- (k+1)/(B+1)
    cp[i, ] <- stats::binom.test(k, B, conf.level = .95)$conf.int
  }
  check(paste0(name, "/fisher_p"), fisher_api, fisher_ref, 1e-7)
  check(paste0(name, "/taxon_holm"), holm_api, stats::p.adjust(fisher_ref, "holm"), 1e-7)
  check(paste0(name, "/taxon_effects"), effect_api, effect_ref)
  check(paste0(name, "/taxon_family_size"), api$multiplicity$taxon$size, length(fisher_ref), 0, 0)
  check(paste0(name, "/omnibus_plusone_p"), lapply(api$pairs, function(p) p$p_value), plusone, 0, 0)
  check(paste0(name, "/omnibus_holm"), lapply(api$pairs, function(p) p$p_value_holm), stats::p.adjust(plusone, "holm"))
  check(paste0(name, "/cp_bounds"), mat(lapply(api$pairs, function(p) p$monte_carlo$tail_probability_interval)), cp)
  envelope <- cbind(stats::p.adjust(cp[, 1L], "holm"), stats::p.adjust(cp[, 2L], "holm"))
  check(paste0(name, "/holm_envelopes"), mat(lapply(api$pairs, function(p) p$monte_carlo$holm_envelope)), envelope)
  exact(paste0(name, "/raw_interval_flags"), lapply(api$pairs, function(p) p$monte_carlo$monte_carlo_unresolved), cp[, 1L] <= .05 & .05 <= cp[, 2L])
  exact(paste0(name, "/holm_envelope_flags"), lapply(api$pairs, function(p) p$monte_carlo$holm_envelope_unresolved), envelope[, 1L] <= .05 & .05 <= envelope[, 2L])
  for (limit in api$zero_count_limits) check(paste0(name, "/zero_count_limit_", limit$sample_id), limit$upper_limit,
    stats::binom.test(0, sum(z[limit$sample_id, ]), alternative = "less", conf.level = .95)$conf.int[2L])
  families[[name]] <- list(n_pairs = length(wanted), n_taxon_tests = length(fisher_ref))
}

receipt <- list(status = if (all(vapply(checks, function(c) c$n_fields == c$n_agree, FALSE))) "pass" else "fail",
  frozen_design_commit = "e20178162d97a832d102b0f39952008292b67ed1", r_version = R.version.string,
  vegan_version = as.character(packageVersion("vegan")), inext_source_sha256 = sha256(inext),
  input_hashes = lapply(setNames(c(source_path, input, file.path(here, "data/samples.csv"), file.path(here, "study.json"), file.path(here, "results.json"), file.path(here, "intake.py"), file.path(here, "analysis.py")), c("saved_source", "count_table", "metadata", "study", "results", "intake_code", "analysis_code")), sha256),
  methods = list(community = "vegan specnumber/diversity/decostand/vegdist", rarefaction = "vegan rarefy(se=TRUE); variance is its squared conditional SD",
                 coverage = "pinned iNEXT Chat.Ind", taxon = "R fisher.test(two.sided) and p.adjust(holm)",
                 omnibus = "plus-one arithmetic from saved exceedances; binom.test CP; p.adjust(holm) separately on bounds"),
  tolerance_rule = "maximum of absolute tolerance and relative tolerance times absolute reference value",
  scope = "Arithmetic and frozen source/design checks only. Does not resample multivariate Monte Carlo tables, test scientific assumptions or independently check PCoA geometry. Fresh API replay is separate.",
  code_audit_scope = "Code hashes are recorded for the separate manual API-use review; this R script does not perform static code analysis",
  reference_warnings = reference_warnings,
  families = families, common_rarefaction_size = m, n_check_groups = length(checks),
  n_fields = sum(vapply(checks, function(c) c$n_fields, 0)), n_agree = sum(vapply(checks, function(c) c$n_agree, 0)),
  max_abs_difference = max(vapply(checks, function(c) c$max_abs_difference, 0)), checks = checks)
writeLines(jsonlite::toJSON(receipt, auto_unbox = TRUE, digits = NA, pretty = TRUE), file.path(here, "reference-check.json"))
cat(receipt$status, receipt$n_agree, "/", receipt$n_fields, "fields; max absolute difference", receipt$max_abs_difference, "\n")
stopifnot(receipt$status == "pass")
