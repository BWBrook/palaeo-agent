args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) %in% c(1L, 2L))
script_arg <- commandArgs()[grepl("^--file=", commandArgs())]
script <- normalizePath(sub("^--file=", "", script_arg))
root <- normalizePath(file.path(dirname(script), ".."))
libraries <- list.dirs(file.path(root, "references/r/renv/library"), recursive = TRUE)
libraries <- libraries[basename(libraries) == R.version$platform &
                         dir.exists(file.path(libraries, "vegan"))]
.libPaths(c(libraries, .libPaths()))
stopifnot(requireNamespace("vegan", quietly = TRUE), requireNamespace("jsonlite", quietly = TRUE))
sha256 <- function(path) {
  strsplit(system2("shasum", c("-a", "256", shQuote(path)), stdout = TRUE), " ")[[1L]][1L]
}
upstream <- normalizePath(args[[1L]])
source_file <- file.path(upstream, "iNEXT.r")
description <- file.path(upstream, "DESCRIPTION")
stopifnot(sha256(source_file) == "ebda76c6f9477c44141900314e94aa0a20498be015afe21877d6d26f170f7619",
          sha256(description) == "73d08ae95e8956b05b5a44db8bf7d0695376d84563ac8b6c2071c9fc57c54be8")
source_env <- new.env(parent = baseenv())
expressions <- parse(source_file)
selected <- Filter(function(e) is.call(e) && as.character(e[[1L]]) %in% c("<-", "=") &&
                     identical(e[[2L]], as.name("Chat.Ind")), as.list(expressions))
stopifnot(length(selected) == 1L)
eval(selected[[1L]], envir = source_env)
coverage <- source_env$Chat.Ind
input_path <- "benchmarks/past/legacy-data/llanvirn.dat"
counts <- t(as.matrix(read.table(file.path(root, input_path), header = TRUE, row.names = 1L,
                                check.names = FALSE, comment.char = "", quote = "")))
stopifnot(all(counts == floor(counts)), all(counts >= 0), !anyNA(counts))
capture_warnings <- function(expr) {
  warnings <- character()
  value <- withCallingHandlers(expr, warning = function(w) {
    warnings <<- c(warnings, conditionMessage(w))
    invokeRestart("muffleWarning")
  })
  list(value = value, warnings = unique(warnings))
}
rare_sample <- function(x, id, sizes) {
  n <- sum(x)
  estimates <- lapply(sizes, function(m) {
    fit <- capture_warnings(vegan::rarefy(x, sample = m, se = TRUE))
    list(size = m, expected_richness = unname(fit$value[1L]),
         variance = unname(fit$value[2L]^2), sd = unname(fit$value[2L]),
         coverage = if (n > 1) unname(coverage(x, m)) else NULL,
         warnings = as.list(fit$warnings))
  })
  list(sample_id = id, counts = as.list(unname(x)), total = n, observed_richness = sum(x > 0),
       f1 = sum(x == 1), f2 = sum(x == 2),
       full_coverage = if (n > 1) unname(coverage(x, n)) else NULL,
       raw_inext_full_coverage = unname(coverage(x, n)),
       coverage_policy = if (n == 1) "coverage_unavailable_single_specimen" else "iNEXT_Chat.Ind",
       estimates = estimates)
}
fixtures <- list(enumeration = c(3, 2, 1, 1), all_singletons = c(1, 1, 1, 1),
                 no_doubletons = c(5, 1, 1), no_singletons = c(4, 2, 2),
                 boundary_one_singleton = c(5, 1), one_taxon = c(7), single_specimen = c(1))
rare <- list(llanvirn = lapply(seq_len(nrow(counts)), function(i)
  rare_sample(counts[i, ], rownames(counts)[i], unique(c(1L, 13L, sum(counts[i, ]))))),
  fixtures = lapply(names(fixtures), function(id) {
    x <- fixtures[[id]]
    rare_sample(x, id, if (id == "enumeration") c(1, 2, 3, 5, 7) else unique(c(1, 2, sum(x)))[unique(c(1, 2, sum(x))) <= sum(x)])
  }))
B <- 9999L
seed <- 7112026L
RNGkind("Mersenne-Twister", "Inversion", "Rejection")
set.seed(seed)
pair_ref <- function(x, ids) {
  table <- t(x)
  absent <- rownames(table)[rowSums(table) == 0]
  table <- table[rowSums(table) > 0, , drop = FALSE]
  fit <- capture_warnings(chisq.test(table, correct = FALSE))
  simulated <- chisq.test(table, simulate.p.value = TRUE, B = B)
  b <- as.integer(round(simulated$p.value * (B + 1) - 1))
  interval <- unname(binom.test(b, B, conf.level = 0.95)$conf.int)
  totals <- colSums(table)
  taxon_tests <- lapply(seq_len(nrow(table)), function(i) {
    cells <- table[i, ]
    ft <- matrix(c(cells[1L], totals[1L] - cells[1L], cells[2L], totals[2L] - cells[2L]), nrow = 2, byrow = TRUE)
    support <- seq.int(max(0, sum(cells) - totals[2L]), min(sum(cells), totals[1L]))
    probs <- dhyper(support, sum(cells), sum(totals) - sum(cells), totals[1L])
    observed <- dhyper(cells[1L], sum(cells), sum(totals) - sum(cells), totals[1L])
    extra <- support[probs > observed * (1 + 1e-14) & probs <= observed * (1 + 1e-7)]
    list(taxon_id = rownames(table)[i], table = unname(ft),
         p_value = fisher.test(ft, alternative = "two.sided")$p.value,
         near_ties_added_by_R_tolerance = as.list(extra))
  })
  list(sample_ids = as.list(ids), taxon_ids = as.list(rownames(table)),
       taxa_absent_from_pair = as.list(absent), observed_counts = unname(table),
       pearson_chi_squared = unname(fit$value$statistic), expected_counts = unname(fit$value$expected),
       p_value = simulated$p.value, taxon_tests = taxon_tests,
       monte_carlo = list(simulations = B, count_extreme = b, tail_probability_interval = interval),
       warnings = as.list(fit$warnings))
}
adjust_family <- function(pairs) {
  adjusted <- p.adjust(vapply(pairs, function(p) p$p_value, numeric(1)), method = "holm")
  taxon_adjusted <- p.adjust(unlist(lapply(pairs, function(p) lapply(p$taxon_tests, function(t) t$p_value))), method = "holm")
  offset <- 0L
  for (i in seq_along(pairs)) {
    pairs[[i]]$p_value_holm <- adjusted[i]
    for (j in seq_along(pairs[[i]]$taxon_tests)) {
      offset <- offset + 1L
      pairs[[i]]$taxon_tests[[j]]$p_value_holm <- unname(taxon_adjusted[offset])
    }
  }
  list(pairs = pairs, omnibus_family_size = length(pairs), taxon_family_size = offset)
}
pairs <- adjust_family(lapply(seq_len(nrow(counts) - 1L), function(i)
  pair_ref(counts[c(i, i + 1L), , drop = FALSE], rownames(counts)[c(i, i + 1L)])))
tiny <- rbind(a = c(2, 1, 0, 0), b = c(0, 1, 2, 0))
colnames(tiny) <- c("t1", "t2", "t3", "absent")
tiny_ref <- adjust_family(list(pair_ref(tiny, rownames(tiny))))
allocations <- as.matrix(expand.grid(t1 = 0:2, t2 = 0:2, t3 = 0:2))
allocations <- allocations[rowSums(allocations) == 3, , drop = FALSE]
weights <- apply(allocations, 1L, function(a) prod(choose(2, a)) / choose(6, 3))
statistics <- apply(allocations, 1L, function(a) unname(suppressWarnings(chisq.test(cbind(a, 2 - a), correct = FALSE))$statistic))
tail <- statistics >= (1 - 64 * .Machine$double.eps) * tiny_ref$pairs[[1L]]$pearson_chi_squared
tiny_ref$exact <- list(first_sample_allocations = unname(allocations), probabilities = weights,
                       statistics = statistics, probability_sum = sum(weights),
                       conditional_tail_probability = sum(weights[tail]), table_count = nrow(allocations))
zero <- lapply(seq_len(nrow(counts)), function(i) list(sample_id = rownames(counts)[i], total = sum(counts[i, ]),
  confidence = 0.95, upper_limit = unname(binom.test(0, sum(counts[i, ]), alternative = "less", conf.level = 0.95)$conf.int[2L]),
  taxon_ids = as.list(colnames(counts)[counts[i, ] == 0 & colSums(counts) > 0])))
interval_controls <- lapply(c(0L, 1L, 500L, 999L, 1000L), function(b) list(count_extreme = b, simulations = 1000L,
  interval = unname(binom.test(b, 1000L, conf.level = 0.95)$conf.int)))
record <- list(reference_kind = "independent_R_library_and_pinned_upstream_source_not_PAST_execution",
  generator = "scripts/reference_assemblages.R", generator_sha256 = sha256(script),
  command = "Rscript --vanilla scripts/reference_assemblages.R /path/to/pinned-iNEXT-source-directory",
  R = R.version.string, packages = list(vegan = as.character(packageVersion("vegan")),
    stats = as.character(packageVersion("stats")), jsonlite = as.character(packageVersion("jsonlite"))),
  input = list(path = input_path, sha256 = sha256(file.path(root, input_path)), orientation = "taxa_by_samples"),
  coverage_reference = list(kind = "unmodified_upstream_function_executed_without_installing_package",
    package = "iNEXT", version = unname(read.dcf(description)[1L, "Version"]), function_name = "Chat.Ind",
    revision = "27ac0343bd4f6133fe585c49a583e7de694cfb58",
    source_url = "https://raw.githubusercontent.com/JohnsonHsieh/iNEXT/27ac0343bd4f6133fe585c49a583e7de694cfb58/R/iNEXT.r",
    source_sha256 = sha256(source_file), description_sha256 = sha256(description),
    single_specimen_policy = "contract deliberately returns null; raw upstream value recorded separately"),
  settings = list(rarefaction = "vegan::rarefy(x, sample=m, se=TRUE); variance=se^2",
    chi_squared = "stats::chisq.test(table, correct=FALSE)", monte_carlo = "stats::chisq.test(table, simulate.p.value=TRUE, B=9999)",
    RNG = as.list(RNGkind()), seed = seed, simulations = B,
    stream = "one sequential R stream in declared pair order; independent from Python streams",
    fisher = "stats::fisher.test(table, alternative='two.sided'); relative probability tolerance 1e-7",
    adjustment = "stats::p.adjust(method='holm'); one omnibus family, one pooled pair-by-taxon family",
    zero_limits = "stats::binom.test(0,n,alternative='less',conf.level=0.95)",
    monte_carlo_intervals = "stats::binom.test(b,B,conf.level=0.95)$conf.int",
    monte_carlo_acceptance = "absolute difference <= 6*sqrt(p_pool*(1-p_pool)*(1/B_R+1/B_Python)) + 2/min(B_R,B_Python); no RNG identity expected"),
  rarefaction = rare, count_homogeneity = pairs, tiny_count_homogeneity = tiny_ref,
  zero_count_limits = zero, monte_carlo_interval_controls = interval_controls)
output <- if (length(args) == 2L) args[[2L]] else file.path(root, "benchmarks/past/references/assemblages-r.json")
jsonlite::write_json(record, output, auto_unbox = TRUE, digits = 17, pretty = TRUE, null = "null")
