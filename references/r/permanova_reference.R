# Independent vegan reference; does not import or invoke Palaeo-Agent.
# Rscript --vanilla references/r/permanova_reference.R [output-json]

arguments <- commandArgs(trailingOnly = FALSE)
script <- normalizePath(sub("^--file=", "", arguments[grepl("^--file=", arguments)]))
script_dir <- dirname(script)
root <- normalizePath(file.path(script_dir, "../.."))
libraries <- list.dirs(file.path(script_dir, "renv/library"), recursive = TRUE)
libraries <- libraries[basename(libraries) == R.version$platform &
                       dir.exists(file.path(libraries, "vegan")) & dir.exists(file.path(libraries, "jsonlite"))]
if (length(libraries) != 1L) stop("One existing project renv library for this R platform is required; no restore is performed")
.libPaths(c(libraries, .libPaths()))
suppressPackageStartupMessages({ library(vegan); library(jsonlite) })
output_args <- commandArgs(trailingOnly = TRUE)
output <- if (length(output_args)) output_args[[1L]] else file.path(script_dir, "permanova-reference.json")
plan_path <- file.path(script_dir, "permanova/cases.json")
plan <- fromJSON(plan_path, simplifyVector = FALSE)
stopifnot(identical(plan$contract_commit, "2c335a7"))

sha256 <- function(path) {
  strsplit(system2("shasum", c("-a", "256", shQuote(path)), stdout = TRUE), " ")[[1L]][1L]
}

read_inputs <- function(case) {
  raw <- read.table(file.path(root, case$input), header = TRUE, check.names = FALSE,
                    colClasses = "character", comment.char = "", quote = "")
  samples <- raw[[1L]]
  taxa <- colnames(raw)[-1L]
  x <- as.matrix(raw[, -1L, drop = FALSE])
  storage.mode(x) <- "double"
  rownames(x) <- samples
  stopifnot(!anyDuplicated(samples), !anyDuplicated(taxa), !anyNA(x),
            all(is.finite(x)), all(x >= 0), all(x == trunc(x)), all(x <= 2^53 - 1), all(rowSums(x) > 0))
  meta <- read.csv(file.path(root, case$metadata), colClasses = "character", check.names = FALSE)
  stopifnot(!anyDuplicated(meta$sample_id), setequal(samples, meta$sample_id))
  groups <- meta$group[match(samples, meta$sample_id)]
  stopifnot(!anyNA(groups), all(nzchar(groups)), all(table(groups) >= 2L))
  list(x = x, samples = samples, taxa = taxa, groups = groups)
}

fit_statistic <- function(d, groups) {
  model <- data.frame(group = factor(groups, levels = unique(groups)))
  fit <- suppressMessages(adonis2(d ~ group, data = model, permutations = 0, sqrt.dist = FALSE, add = FALSE, by = NULL))
  list(pseudo_f = unname(fit$F[1L]), r_squared = unname(fit$R2[1L]),
       ss_total = unname(fit$SumOfSqs[3L]), ss_within = unname(fit$SumOfSqs[2L]),
       ss_between = unname(fit$SumOfSqs[1L]), df_between = unname(fit$Df[1L]), df_within = unname(fit$Df[2L]))
}

classify_statistic <- function(statistic) {
  threshold <- 64 * .Machine$double.eps * statistic$ss_total
  if (statistic$ss_within <= threshold && statistic$ss_between > 0)
    return(list(value = NA_real_, status = "positive_infinity"))
  if (!is.finite(statistic$pseudo_f)) stop("Undefined permuted statistic in independent reference")
  list(value = statistic$pseudo_f, status = "finite")
}

dispersion_reference <- function(d, groups, samples) {
  warnings <- character()
  squared <- as.matrix(d)^2
  centred <- sweep(sweep(squared, 2L, colMeans(squared)), 1L, rowMeans(squared)) + mean(squared)
  all_eigenvalues <- eigen(-centred / 2, symmetric = TRUE, only.values = TRUE)$values
  threshold <- max(sqrt(.Machine$double.eps), sqrt(.Machine$double.eps) * all_eigenvalues[1L])
  fit <- tryCatch(withCallingHandlers(
    betadisper(d, factor(groups, levels = unique(groups)), type = "centroid",
               bias.adjust = FALSE, sqrt.dist = FALSE, add = FALSE),
    warning = function(w) { warnings <<- c(warnings, conditionMessage(w)); invokeRestart("muffleWarning") }),
    error = function(e) e)
  if (inherits(fit, "error")) {
    if (any(abs(all_eigenvalues) > threshold)) stop(fit)
    return(list(status = "native_betadisper_error", native_error = conditionMessage(fit),
      type = "centroid", bias_adjust = FALSE, sqrt_dist = FALSE, add = FALSE,
      threshold = threshold, eigenvalues = unname(all_eigenvalues), retained_positive_axes = 0L, retained_negative_axes = 0L,
      interpretation = "Native centroidFUN fails with no retained axes; no native distance agreement claimed",
      zero_mode_contract_control = list(distances = rep(0, length(samples)), squared_distances = rep(0, length(samples)),
        group_mean_distances = as.list(setNames(rep(0, length(unique(groups))), unique(groups))),
        negative_squared_count = 0L, truncated_sample_ids = list(),
        source = "All axes fall below the frozen eigenvalue threshold, so empty signed coordinate sums are zero")))
  }
  positive <- fit$eig > 0
  centres <- fit$centroids[groups, , drop = FALSE]
  positive_squared <- rowSums((fit$vectors[, positive, drop = FALSE] - centres[, positive, drop = FALSE])^2)
  negative_squared <- rowSums((fit$vectors[, !positive, drop = FALSE] - centres[, !positive, drop = FALSE])^2)
  signed <- positive_squared - negative_squared
  stopifnot(isTRUE(all.equal(as.numeric(fit$distances), unname(sqrt(pmax(signed, 0))), tolerance = 1e-12)))
  list(status = "native_output", type = "centroid", bias_adjust = FALSE, sqrt_dist = FALSE, add = FALSE,
       samples = samples, distances = unname(fit$distances), squared_distances = unname(signed),
       group_mean_distances = as.list(fit$group.distances),
       negative_squared_count = sum(signed < 0), truncated_sample_ids = unname(as.list(samples[signed < 0])),
       threshold = threshold, eigenvalues = unname(all_eigenvalues), retained_eigenvalues = unname(as.list(fit$eig)),
       retained_positive_axes = sum(positive), retained_negative_axes = sum(!positive), warnings = unname(as.list(warnings)))
}

generate_case <- function(case) {
  message("case ", case$id)
  data <- read_inputs(case)
  x <- data$x
  if (case$transform == "relative_abundance") x <- decostand(x, "total")
  d <- if (case$distance == "jaccard") vegdist(x, "jaccard", binary = TRUE) else vegdist(x, "bray")
  distance_reference <- "vegan::vegdist"
  native_distance_observation <- NULL
  analytic_distance_control <- NULL
  if (case$id == "tiny4_bray_exact") {
    stopifnot(all(d == 0))
    native_distance_observation <- list(status = "zero_total_variation", distances = unname(as.matrix(d)),
      ss_total = 0, documented_ZAP = 1e-15, vegan_version = as.character(packageVersion("vegan")),
      source = "vegan::vegdist source: ZAP <- 1e-15; d[d < ZAP] <- 0",
      interpretation = "Explained comparator preprocessing difference; no native vegdist agreement claimed")
    control_path <- file.path(script_dir, "permanova/tiny4-exact-distances.json")
    control <- fromJSON(control_path, simplifyVector = FALSE)
    stopifnot(control$input_sha256 == sha256(file.path(root, case$input)),
              identical(as.numeric(unlist(control$count_strings)), as.numeric(data$x[, 1L])))
    precise <- do.call(rbind, lapply(control$decimal_distances, function(row) as.numeric(unlist(row))))
    dimnames(precise) <- list(data$samples, data$samples)
    d <- as.dist(precise)
    distance_reference <- "Exact rational Bray-Curtis converted from 80-digit decimal strings, supplied directly to adonis2"
    analytic_distance_control <- list(path = "references/r/permanova/tiny4-exact-distances.json",
                                      sha256 = sha256(control_path), formula = control$formula)
  }
  observed <- fit_statistic(d, data$groups)
  stopifnot(observed$ss_total > 0, observed$ss_within > 64 * .Machine$double.eps * observed$ss_total)
  schedule <- fromJSON(file.path(root, case$schedule), simplifyVector = FALSE)
  indices <- do.call(rbind, lapply(schedule$indices, as.integer)) + 1L
  stopifnot(schedule$index_base == 0L, schedule$index_semantics == "distance_matrix_reordering_fixed_groups",
            identical(unlist(schedule$sample_ids), data$samples), identical(unlist(schedule$groups), data$groups),
            schedule$input_sha256 == sha256(file.path(root, case$input)),
            schedule$metadata_sha256 == sha256(file.path(root, case$metadata)))
  stopifnot(all(apply(indices, 1L, function(row) identical(sort(row), seq_along(data$samples)))))
  matrix <- as.matrix(d)
  statistics <- lapply(seq_len(nrow(indices)), function(i) {
    take <- indices[i, ]
    fit_statistic(as.dist(matrix[take, take, drop = FALSE]), data$groups)
  })
  classified <- lapply(statistics, classify_statistic)
  values <- vapply(classified, `[[`, 0.0, "value")
  statuses <- vapply(classified, `[[`, "", "status")
  tie_tolerance <- sqrt(.Machine$double.eps)
  extremes <- statuses == "positive_infinity" | (!is.na(values) & values >= observed$pseudo_f - tie_tolerance)
  observed_row <- which(apply(indices, 1L, function(row) identical(row, seq_along(data$samples))))
  observed_allocations <- which(apply(indices, 1L, function(row) identical(data$groups[order(row)], data$groups)))
  if (schedule$mode == "exact") {
    stopifnot(length(observed_row) == 1L, length(observed_allocations) == 1L, nrow(indices) == schedule$space_size)
    allocations <- apply(indices, 1L, function(row) paste(data$groups[order(row)], collapse = "|"))
    stopifnot(!anyDuplicated(allocations))
    denominator <- nrow(indices)
    p_value <- sum(extremes) / denominator
    native_indices <- indices[-observed_row, , drop = FALSE]
    native_target <- values[-observed_row]
    native_statuses <- statuses[-observed_row]
  } else {
    denominator <- nrow(indices) + 1L
    p_value <- (sum(extremes) + 1L) / denominator
    native_indices <- indices
    native_target <- values
    native_statuses <- statuses
  }
  model <- data.frame(group = factor(data$groups, levels = unique(data$groups)))
  native_fit <- adonis2(d ~ group, data = model, permutations = native_indices,
                        sqrt.dist = FALSE, add = FALSE, by = NULL)
  native_permuted <- as.numeric(attr(native_fit, "F.perm"))
  finite <- native_statuses == "finite" & is.finite(native_permuted)
  native_max_error <- if (any(finite)) max(abs(native_permuted[finite] - native_target[finite])) else 0
  native_p <- unname(native_fit$`Pr(>F)`[1L])
  list(id = case$id, input = case$input, metadata = case$metadata,
       input_sha256 = sha256(file.path(root, case$input)), metadata_sha256 = sha256(file.path(root, case$metadata)),
       distance = case$distance, transform = case$transform,
       distance_reference = distance_reference, native_distance_observation = native_distance_observation,
       analytic_distance_control = analytic_distance_control,
       sample_ids = data$samples, taxon_ids = unname(as.list(data$taxa)), groups = data$groups,
       group_sizes = as.list(table(factor(data$groups, levels = unique(data$groups)))),
       distances = unname(as.matrix(d)), observed = observed,
       permutation = list(mode = schedule$mode, requested = case$permutations, draws = nrow(indices),
          space_size = schedule$space_size, count_extreme = sum(extremes), denominator = denominator,
          p_value = p_value, seed = case$seed, bit_generator = schedule$bit_generator,
          numpy_version = schedule$numpy_version, index_base = 0L,
          index_semantics = schedule$index_semantics, indices = indices - 1L,
          statistics = values, statuses = statuses, infinite_count = sum(statuses == "positive_infinity"),
          identity_index_rows = unname(as.list(observed_row - 1L)),
          observed_label_allocation_rows = unname(as.list(observed_allocations - 1L)), tie_tolerance = tie_tolerance,
          schedule_path = case$schedule, schedule_sha256 = sha256(file.path(root, case$schedule))),
       native_adonis2 = list(p_value = native_p, p_agrees_with_declared_counting = abs(native_p - p_value) <= 1e-14,
          supplied_draws = nrow(native_indices), observed_excluded_from_exact_native_schedule = schedule$mode == "exact",
          maximum_finite_statistic_difference = native_max_error,
          permuted_statistics = ifelse(is.finite(native_permuted), native_permuted, NA_real_),
          permuted_statuses = ifelse(is.finite(native_permuted), "finite", ifelse(native_permuted > 0, "positive_infinity", "undefined"))),
       dispersion = dispersion_reference(d, data$groups, data$samples))
}

cases <- lapply(plan$cases, generate_case)
record <- list(kind = "independent_vegan_permanova_reference", contract_commit = plan$contract_commit,
  contract_sha256 = sha256(file.path(root, plan$contract_path)), generator = "references/r/permanova_reference.R",
  generator_sha256 = sha256(script), generated_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
  r_version = R.version.string, platform = R.version$platform, lapack = La_version(),
  packages = list(vegan = as.character(packageVersion("vegan")), permute = as.character(packageVersion("permute")),
                  jsonlite = as.character(packageVersion("jsonlite"))),
  rtol = plan$rtol, atol = plan$atol,
  definitions = list(adonis2 = "adonis2(distance ~ group, sqrt.dist=FALSE, add=FALSE, by=NULL)",
    exact = "Every unique labelled group allocation once, observed once: count(Fperm >= Fobs - sqrt(eps))/M",
    monte_carlo = "Stored NumPy PCG64 index schedule; distances[index,index], groups fixed; plus-one p",
    dispersion = "betadisper(type='centroid', bias.adjust=FALSE, sqrt.dist=FALSE, add=FALSE)",
    independence = "Independent vegan implementations and R parser; not independence of shared LAPACK or method definitions"),
  cases = cases,
  scope = "Known synthetic development cases; not blind or held-out evidence, not a PAST comparison")
writeLines(toJSON(record, auto_unbox = TRUE, digits = I(17), pretty = TRUE, null = "null", na = "null", matrix = "rowmajor"), output)
cat("wrote", output, "\n")
