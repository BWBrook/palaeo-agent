# vegan keys for the blind PERMANOVA fixtures: betadisper centroid distances and an
# adonis2 cross-check of F and R2 (and exact p by full permutation for n <= 8).
# Run from palaeo-agent/references/r so renv supplies the locked vegan:
#   Rscript <this file> <fixtures dir> <output json>

suppressPackageStartupMessages({
  library(vegan)
  library(jsonlite)
  library(permute)
})

args <- commandArgs(trailingOnly = TRUE)
fixdir <- args[1]
out_path <- args[2]
spec <- fromJSON(file.path(fixdir, "fixtures.json"), simplifyVector = FALSE)

read_matrix <- function(path) {
  raw <- read.table(path, header = TRUE, sep = "\t", check.names = FALSE, colClasses = "character",
                    comment.char = "", quote = "")
  x <- as.matrix(raw[, -1, drop = FALSE])
  storage.mode(x) <- "double"
  rownames(x) <- raw[[1]]
  x
}

out <- list(vegan = as.character(packageVersion("vegan")), R = R.version.string, fixtures = list())
for (fx in spec$fixtures) {
  if (!(fx$expect$outcome %in% c("result", "judgment_result"))) next
  x <- read_matrix(file.path(fixdir, fx$matrix))
  groups <- read.csv(file.path(fixdir, fx$groups), colClasses = "character")
  group <- factor(groups$group[match(rownames(x), groups$sample_id)])
  if (fx$transform == "relative_abundance") x <- decostand(x, "total")
  d <- if (fx$distance == "braycurtis") vegdist(x, "bray") else vegdist(x, "jaccard", binary = TRUE)
  bd <- betadisper(d, group, type = "centroid", bias.adjust = FALSE)
  rec <- list(
    dispersion_distances = as.list(setNames(as.numeric(bd$distances), rownames(x))),
    dispersion_group_means = as.list(tapply(bd$distances, group, mean)),
    eigenvalues = as.numeric(bd$eig),
    negative_eigenvalue_count = sum(bd$eig < 0)
  )
  n <- nrow(x)
  df <- data.frame(group = group)
  if (n <= 8) {
    perms <- allPerms(n, control = how(maxperm = 50000))
    a <- adonis2(d ~ group, data = df, permutations = perms)
    rec$adonis2_p_allperms <- a$`Pr(>F)`[1]
    rec$allperms_rows <- nrow(perms)
  } else {
    a <- adonis2(d ~ group, data = df, permutations = 0)
  }
  rec$adonis2_F <- a$F[1]
  rec$adonis2_R2 <- a$R2[1]
  rec$adonis2_SS <- a$SumOfSqs
  out$fixtures[[fx$id]] <- rec
}
writeLines(toJSON(out, auto_unbox = TRUE, digits = NA, pretty = TRUE), out_path)
cat("vegan keys for", length(out$fixtures), "fixtures\n")
