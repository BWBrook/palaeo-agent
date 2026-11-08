args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1)
d <- args[[1]]
a <- read.csv(file.path(d, "cp.csv"))
a$ref_lo <- a$ref_hi <- a$qbeta_lo <- a$qbeta_hi <- NA_real_
for (i in seq_len(nrow(a))) {
  b <- a$b[i]
  B <- a$B[i]
  v <- stats::binom.test(b, B, conf.level = .95)$conf.int
  a$ref_lo[i] <- v[1]
  a$ref_hi[i] <- v[2]
  a$qbeta_lo[i] <- if (b == 0) 0 else stats::qbeta(.025, b, B - b + 1)
  a$qbeta_hi[i] <- if (b == B) 1 else stats::qbeta(.975, b + 1, B - b)
}
a$ref_unresolved <- as.integer(a$ref_lo <= .05 & .05 <= a$ref_hi)
a$error_lo <- abs(a$lo - a$ref_lo)
a$error_hi <- abs(a$hi - a$ref_hi)
a$passed <- a$error_lo <= 1e-12 & a$error_hi <= 1e-12 & a$unresolved == a$ref_unresolved
write.csv(a, file.path(d, "r-reference.csv"), row.names = FALSE)
cat("Cases:", nrow(a), "checked fields:", 3 * nrow(a),
    "max interval error:", max(a$error_lo, a$error_hi), "\n")
cat(R.version.string, "\n")
stopifnot(all(a$passed))
