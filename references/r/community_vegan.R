# Independent vegan reference for the Llanvirn community workflow.
# Run from references/r: Rscript community_vegan.R
# Reads the frozen legacy file with its own parser and writes community-vegan.json.

suppressPackageStartupMessages({
  library(vegan)
  library(jsonlite)
})

input <- normalizePath("../../benchmarks/past/legacy-data/llanvirn.dat")
output <- "community-vegan.json"
k <- 2L
gap_threshold <- 1e-8

sha256 <- function(path) {
  strsplit(system2("shasum", c("-a", "256", shQuote(path)), stdout = TRUE), " ")[[1]][1]
}

raw <- read.table(input, header = TRUE, check.names = FALSE, colClasses = "character",
                  comment.char = "", quote = "")
taxa <- raw[[1]]
counts_taxa_by_samples <- as.matrix(raw[, -1])
storage.mode(counts_taxa_by_samples) <- "integer"
rownames(counts_taxa_by_samples) <- taxa
x <- t(counts_taxa_by_samples)
stopifnot(!anyNA(x), all(x >= 0), all(rowSums(x) > 0))
samples <- rownames(x)

diversity_table <- data.frame(
  sample_id = samples,
  total = as.numeric(rowSums(x)),
  richness = as.integer(specnumber(x)),
  shannon = as.numeric(diversity(x, index = "shannon")),
  simpson = as.numeric(diversity(x, index = "simpson"))
)

pcoa <- function(d) {
  fit <- wcmdscale(d, eig = TRUE)
  eig <- sort(fit$eig, decreasing = TRUE)
  points <- fit$points
  positive_gram <- points %*% t(points)
  gap <- (eig[k] - eig[k + 1]) / eig[1]
  selected <- if (gap > gap_threshold) points[, seq_len(k), drop = FALSE] %*% t(points[, seq_len(k), drop = FALSE]) else NULL
  list(eigenvalues = eig, positive_axes = ncol(points), positive_gram = unname(positive_gram),
       relative_eigengap = gap, selected_gram = if (is.null(selected)) NULL else unname(selected))
}

cases <- list(
  list(id = "braycurtis_relative_abundance", transform = "relative_abundance", distance = "braycurtis",
       call = 'vegdist(decostand(x, "total"), method = "bray")',
       d = vegdist(decostand(x, "total"), method = "bray")),
  list(id = "braycurtis_none", transform = "none", distance = "braycurtis",
       call = 'vegdist(x, method = "bray")',
       d = vegdist(x, method = "bray")),
  list(id = "jaccard_none", transform = "none", distance = "jaccard",
       call = 'vegdist(x, method = "jaccard", binary = TRUE)',
       d = vegdist(x, method = "jaccard", binary = TRUE))
)

totals <- rowSums(x)
imbalance <- abs(outer(totals, totals, "-")) / outer(totals, totals, "+")
raw_bc <- as.matrix(cases[[2]]$d)
stopifnot(all(raw_bc >= imbalance - 1e-12))

case_records <- lapply(cases, function(case) {
  c(list(id = case$id, transform = case$transform, distance = case$distance, vegan_call = case$call,
         distances = unname(as.matrix(case$d))), pcoa(case$d))
})
names(case_records) <- vapply(cases, `[[`, "", "id")

controls <- local({
  identical_rows <- rbind(a = c(3, 1, 0, 2), b = c(3, 1, 0, 2))
  disjoint <- rbind(a = c(4, 2, 0, 0), b = c(0, 0, 5, 1))
  proportional <- rbind(a = c(2, 4, 6, 0), b = c(5, 10, 15, 0))
  nx <- sum(proportional["a", ]); ny <- sum(proportional["b", ])
  list(
    identical_rows = list(matrix = unname(identical_rows),
                          bray = as.numeric(vegdist(identical_rows, "bray")), expected_bray = 0,
                          jaccard_binary = as.numeric(vegdist(identical_rows, "jaccard", binary = TRUE)), expected_jaccard = 0),
    disjoint_supports = list(matrix = unname(disjoint),
                             bray = as.numeric(vegdist(disjoint, "bray")), expected_bray = 1,
                             jaccard_binary = as.numeric(vegdist(disjoint, "jaccard", binary = TRUE)), expected_jaccard = 1),
    proportional_rows = list(matrix = unname(proportional),
                             bray_relative = as.numeric(vegdist(decostand(proportional, "total"), "bray")), expected_bray_relative = 0,
                             bray_raw = as.numeric(vegdist(proportional, "bray")), expected_bray_raw = abs(nx - ny) / (nx + ny))
  )
})
for (control in controls) {
  observed <- unlist(control[!grepl("^(expected_|matrix)", names(control))])
  expected <- unlist(control[grepl("^expected_", names(control))])
  stopifnot(isTRUE(all.equal(unname(observed), unname(expected), tolerance = 1e-14)))
}

record <- list(
  kind = "independent_r_reference",
  generator = "references/r/community_vegan.R",
  command = "cd references/r && Rscript community_vegan.R",
  generated_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
  r_version = R.version.string,
  packages = list(vegan = as.character(packageVersion("vegan")),
                  permute = as.character(packageVersion("permute")),
                  jsonlite = as.character(packageVersion("jsonlite"))),
  platform = R.version$platform,
  lapack = La_version(),
  input = list(path = "benchmarks/past/legacy-data/llanvirn.dat", sha256 = sha256(input),
               orientation = "taxa_by_samples", parser = "utils::read.table, character labels, check.names = FALSE"),
  definitions = list(
    total = "rowSums(x)", richness = "vegan::specnumber(x)",
    shannon = 'vegan::diversity(x, "shannon"), natural log',
    simpson = 'vegan::diversity(x, "simpson") = 1 - sum(p^2)',
    pcoa = "vegan::wcmdscale(d, eig = TRUE): unweighted classical scaling of -0.5 J D^2 J; positive axes only in points",
    positive_gram = "points %*% t(points) over all positive axes",
    selected_gram = sprintf("first %d axes, reported only when (eig[k] - eig[k+1]) / eig[1] > %g", k, gap_threshold)
  ),
  dimensions = k,
  sample_ids = samples,
  taxon_ids = taxa,
  diversity = diversity_table,
  cases = case_records,
  raw_braycurtis_respects_total_imbalance_bound = TRUE,
  analytical_controls = controls,
  scope = paste("Cross-implementation agreement with vegan on one development dataset;",
                "not method validation, not a PAST comparison and not held-out evidence.")
)

writeLines(toJSON(record, auto_unbox = TRUE, digits = I(17), pretty = TRUE, null = "null", matrix = "rowmajor"),
           output)
cat("wrote", output, "\n")
