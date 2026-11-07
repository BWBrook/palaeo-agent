# Independent R reference for the Lake Selina quantities (primer section 7 cross-check).
# Run from the repository root:
#   Rscript --vanilla analyses/lake-selina/reference.R /path/to/pinned-iNEXT-source-directory
# Writes analyses/lake-selina/reference-r.json. vegan for diversity, distances and rarefaction;
# the pinned iNEXT Chat.Ind for coverage; stats::fisher.test for the named-pair taxon tests.
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
source_file <- file.path(normalizePath(args[[1L]]), "iNEXT.r")
stopifnot(sha256(source_file) == "ebda76c6f9477c44141900314e94aa0a20498be015afe21877d6d26f170f7619")
env <- new.env(parent = baseenv())
exprs <- parse(source_file)
sel <- Filter(function(e) is.call(e) && as.character(e[[1L]]) %in% c("<-", "=") &&
                identical(e[[2L]], as.name("Chat.Ind")), as.list(exprs))
stopifnot(length(sel) == 1L)
eval(sel[[1L]], envir = env)
coverage <- env$Chat.Ind

input <- file.path(here, "data/counts.tsv")
x <- as.matrix(read.delim(input, row.names = 1L, check.names = FALSE, colClasses = c("character")))
storage.mode(x) <- "numeric"
stopifnot(all(x == floor(x)), all(x >= 0), !anyNA(x))
design <- jsonlite::fromJSON(file.path(here, "design.json"), simplifyVector = FALSE)
m <- design$specs$rarefaction$sizes[[1L]]

per_sample <- lapply(seq_len(nrow(x)), function(i) {
  v <- x[i, ]
  r <- vegan::rarefy(v, sample = m, se = TRUE)
  list(sample_id = rownames(x)[i], total = sum(v), richness = sum(v > 0),
       shannon = unname(vegan::diversity(v, "shannon")), simpson = unname(vegan::diversity(v, "simpson")),
       expected_richness = unname(r[1L]), conditional_sd = unname(r[2L]),
       coverage_at_m = unname(coverage(v, m)), full_coverage = unname(coverage(v, sum(v))))
})
mat <- function(d) unname(as.matrix(d))
distances <- list(
  relative_braycurtis = mat(vegan::vegdist(vegan::decostand(x, "total"), "bray")),
  raw_braycurtis = mat(vegan::vegdist(x, "bray")),
  binary_jaccard = mat(vegan::vegdist(x, "jaccard", binary = TRUE)))

named <- c(design$named_comparisons, list())
pairs <- lapply(names(design$named_comparisons), function(k) {
  ids <- vapply(design$named_comparisons[[k]]$endpoints, function(e) e$sample_id, "")
  a <- x[ids[1L], ]; b <- x[ids[2L], ]
  present <- which(a + b > 0)
  list(comparison = k, sample_ids = as.list(ids), taxa = lapply(present, function(j) {
    ft <- matrix(c(a[j], sum(a) - a[j], b[j], sum(b) - b[j]), nrow = 2L)
    list(taxon = colnames(x)[j], counts = c(a[j], b[j]),
         p_value = fisher.test(ft, alternative = "two.sided")$p.value)
  }))
})

record <- list(input_sha256 = sha256(input), r_version = R.version.string,
               vegan_version = as.character(packageVersion("vegan")), inext_source_sha256 = sha256(source_file),
               settings = list(rarefaction = "vegan::rarefy(x, sample=m, se=TRUE)",
                               coverage = "iNEXT Chat.Ind(x, m) from pinned source",
                               relative_braycurtis = "vegdist(decostand(x, 'total'), 'bray')",
                               jaccard = "vegdist(x, 'jaccard', binary=TRUE)",
                               fisher = "fisher.test(2x2 taxon vs rest, two.sided)"),
               size = m, samples = per_sample, distances = distances, named_pair_fisher = pairs)
writeLines(jsonlite::toJSON(record, auto_unbox = TRUE, digits = NA, pretty = TRUE), file.path(here, "reference-r.json"))
