# Independent rioja arithmetic on canonical coordinates supplied by reference.py.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
script <- normalizePath(sub('^--file=', '', grep('^--file=', commandArgs(), value = TRUE)))
repo <- normalizePath(file.path(dirname(script), '../..'))
reference_dir <- file.path(repo, 'references/r')
libraries <- list.dirs(file.path(reference_dir, 'renv/library'), recursive = TRUE)
libraries <- libraries[basename(libraries) == R.version$platform &
                       dir.exists(file.path(libraries, 'rioja')) & dir.exists(file.path(libraries, 'jsonlite'))]
if (length(libraries) != 1L) stop('Exactly one existing project R library is required; no restore is performed')
.libPaths(c(libraries, .libPaths()))
suppressPackageStartupMessages({ library(rioja); library(vegan); library(jsonlite) })
lock <- fromJSON(file.path(reference_dir, 'renv.lock'), simplifyVector = FALSE)
for (package in c('rioja', 'vegan', 'jsonlite')) {
  stopifnot(package_version(as.character(packageVersion(package))) == package_version(lock$Packages[[package]]$Version))
}
stopifnot(packageVersion('rioja') == '1.0.7')
input <- fromJSON(args[1], simplifyVector = FALSE)

run_case <- function(case) {
  x <- do.call(rbind, lapply(case$coordinates, function(row) as.numeric(unlist(row))))
  n <- nrow(x)
  stopifnot(n >= 3L, n == length(case$sample_ids), all(is.finite(x)))
  dissimilarity <- dist(x)^2
  tree <- chclust(dissimilarity, 'coniss')
  per_boundary <- .Call('chclust_c', as.matrix(dissimilarity), 2L, PACKAGE = 'rioja')
  partitions <- lapply(seq_len(n), function(k) {
    labels <- as.integer(cutree(tree, k))
    as.integer(match(labels, unique(labels)))
  })
  m <- n - 1L
  stick <- bstick(tree, ng = n - 1L, plot = FALSE)
  gains <- c(as.numeric(stick$dispersion), min(tree$height))
  expected <- c(as.numeric(stick$bstick), bstick(m, max(tree$height))[m])
  stopifnot(length(gains) == m, length(expected) == m, length(per_boundary) == m)
  exceeds <- gains > expected
  failures <- which(!exceeds)
  selected <- if (length(failures)) failures[1L] else n
  merge_steps <- integer(m)
  merge_steps[order(per_boundary, seq_len(m))] <- seq_len(m)
  list(id = unbox(case$id), sample_ids = as.character(unlist(case$sample_ids)),
       call = unbox("chclust(dist(X)^2, 'coniss'); unsorted chclust_c; cutree at every k; bstick plus final rank"),
       per_boundary = as.numeric(per_boundary), total_dispersion = unbox(max(tree$height)),
       split_ranks = as.integer(m - merge_steps + 1L), partitions = partitions,
       gains = as.numeric(gains), expectations = as.numeric(expected),
       exceeds = as.logical(exceeds), selected_zones = unbox(as.integer(selected)))
}

result <- list(r_version = unbox(R.version.string),
               packages = list(rioja = unbox(as.character(packageVersion('rioja'))),
                               vegan = unbox(as.character(packageVersion('vegan'))),
                               jsonlite = unbox(as.character(packageVersion('jsonlite')))),
               cases = lapply(input$cases, run_case))
writeLines(toJSON(result, digits = I(17), pretty = TRUE), args[2])
