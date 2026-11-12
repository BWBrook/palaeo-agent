# Independent rioja 1.0-7 CONISS reference; does not import or invoke Palaeo-Agent.
# Rscript --vanilla references/r/coniss_reference.R [output-json]
# Input: references/r/coniss/cases.json (coordinates written by coniss/make_cases.py).

arguments <- commandArgs(trailingOnly = FALSE)
script <- normalizePath(sub("^--file=", "", arguments[grepl("^--file=", arguments)]))
script_dir <- dirname(script)
libraries <- list.dirs(file.path(script_dir, "renv/library"), recursive = TRUE)
libraries <- libraries[basename(libraries) == R.version$platform &
                       dir.exists(file.path(libraries, "rioja")) & dir.exists(file.path(libraries, "jsonlite"))]
if (length(libraries) != 1L) stop("One existing project renv library for this R platform is required; no restore is performed")
.libPaths(c(libraries, .libPaths()))
suppressPackageStartupMessages({ library(rioja); library(vegan); library(jsonlite) })
stopifnot(packageVersion("rioja") == "1.0.7")
output_args <- commandArgs(trailingOnly = TRUE)
output <- if (length(output_args)) output_args[[1L]] else file.path(script_dir, "coniss-reference.json")
plan_path <- file.path(script_dir, "coniss/cases.json")
plan <- fromJSON(plan_path, simplifyVector = FALSE)

sha256 <- function(path) strsplit(system2("shasum", c("-a", "256", shQuote(path)), stdout = TRUE), " ")[[1L]][1L]

run_case <- function(case) {
  x <- do.call(rbind, lapply(case$coordinates, function(row) as.numeric(unlist(row))))
  n <- nrow(x)
  d <- dist(x)^2
  tree <- chclust(d, "coniss")
  per_boundary <- .Call("chclust_c", as.matrix(d), 2L, PACKAGE = "rioja")
  partitions <- lapply(seq_len(n), function(k) as.integer(cutree(tree, k)))
  m <- n - 1L
  stick <- if (m >= 2L) bstick(tree, ng = n - 1L, plot = FALSE) else data.frame(nGroups = integer(), dispersion = numeric(), bstick = numeric())
  list(id = unbox(case$id), n = unbox(n), call = unbox("chclust(dist(X)^2, 'coniss'); .Call('chclust_c', as.matrix(d), 2L)"),
       per_boundary = as.numeric(per_boundary), sorted_height = as.numeric(tree$height),
       partitions = partitions,
       bstick = list(groups = as.integer(stick$nGroups), dispersion = as.numeric(stick$dispersion),
                     expected = as.numeric(stick$bstick)),
       final_rank = list(gain = unbox(min(tree$height)), expected = unbox(bstick(m, max(tree$height))[m])))
}

result <- list(
  generator = unbox("references/r/coniss_reference.R"), cases_sha256 = unbox(sha256(plan_path)),
  r_version = unbox(R.version.string), packages = list(rioja = unbox(as.character(packageVersion("rioja"))),
                                                       vegan = unbox(as.character(packageVersion("vegan"))),
                                                       jsonlite = unbox(as.character(packageVersion("jsonlite")))),
  rtol = unbox(1e-10), cases = lapply(plan$cases, run_case))
writeLines(toJSON(result, digits = I(17), pretty = TRUE), output)
