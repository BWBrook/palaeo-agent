args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
input <- args[[1L]]
output <- args[[2L]]
table <- read.table(input, header = TRUE, row.names = 1L,
                    check.names = FALSE, na.strings = ".")
counts <- t(as.matrix(table))
stopifnot(!anyNA(counts), all(is.finite(counts)), all(counts >= 0),
          all(counts == floor(counts)), all(rowSums(counts) > 0))
totals <- rowSums(counts)
proportions <- counts / totals
entropy_terms <- proportions
entropy_terms[proportions > 0] <- -proportions[proportions > 0] *
  log(proportions[proportions > 0])
diversity <- data.frame(sample_id = rownames(counts), total = totals,
                        richness = rowSums(counts > 0),
                        shannon = rowSums(entropy_terms),
                        simpson = 1 - rowSums(proportions^2), row.names = NULL)
cases <- list()
for (transform in c("none", "relative_abundance")) {
  values <- if (transform == "none") counts else proportions
  for (metric in c("braycurtis", "jaccard")) {
    if (metric == "jaccard" && transform != "none") next
    if (metric == "braycurtis") {
      distances <- as.matrix(dist(values, method = "manhattan")) /
        outer(rowSums(values), rowSums(values), "+")
    } else {
      distances <- as.matrix(dist(values > 0, method = "binary"))
    }
    warnings <- character()
    fit <- withCallingHandlers(
      cmdscale(as.dist(distances), k = nrow(values) - 1L, eig = TRUE, add = FALSE),
      warning = function(w) {
        warnings <<- c(warnings, conditionMessage(w))
        invokeRestart("muffleWarning")
      }
    )
    cases[[length(cases) + 1L]] <- list(
      transform = transform, distance = metric,
      sample_ids = unname(rownames(counts)), taxon_ids = unname(colnames(counts)),
      diversity = diversity, distances = unname(distances),
      eigenvalues = unname(fit$eig),
      positive_gram = unname(tcrossprod(fit$points)),
      warnings = warnings
    )
  }
}
record <- list(reference_kind = "base_R_stats_library_comparison_not_PAST_execution",
               input = input, R = R.version.string,
               packages = list(stats = as.character(packageVersion("stats")),
                               jsonlite = as.character(packageVersion("jsonlite"))),
               rtol = 1e-10, atol = 1e-10, cases = cases)
jsonlite::write_json(record, output, auto_unbox = TRUE, digits = 17, pretty = TRUE)
