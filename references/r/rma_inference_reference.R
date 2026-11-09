# Independent references for rma inference (sprint 13): smatr for ordinary values, base R for log tails.
# Run from references/r: Rscript rma_inference_reference.R
library(smatr)
library(jsonlite)

read_past <- function(path) {
  table <- read.table(path, header = TRUE, sep = "", check.names = FALSE, colClasses = "character",
                      na.strings = ".", comment.char = "")
  table
}
digest <- function(path) unname(tools::md5sum(path))  # informational; SHA-256 is pinned by the Python test

cases <- list(
  list(id = "dielasma_L1_log", input = "../../benchmarks/past/legacy-data/dielasma.dat", x = "L1/X1", y = "L1/X2", log = TRUE, k = 1),
  list(id = "dielasma_L3_log", input = "../../benchmarks/past/legacy-data/dielasma.dat", x = "L3/X1", y = "L3/X2", log = TRUE, k = 1),
  list(id = "limpet_caliper_log", input = "../../analyses/fossil-limpets/measurements.tsv", x = "Length_Caliper_mm", y = "Width_Caliper_mm", log = TRUE, k = 1),
  list(id = "limpet_automorph_log", input = "../../analyses/fossil-limpets/measurements.tsv", x = "MajorAxisLength_AutoMorph_mm", y = "MinorAxisLength_AutoMorph_mm", log = TRUE, k = 1),
  list(id = "negative_raw", input = "rma/negative.dat", x = "x", y = "y", log = FALSE, k = 1.5),
  list(id = "three_raw", input = "rma/three.dat", x = "x", y = "y", log = FALSE, k = 1),
  list(id = "raw_magnitude_two", input = "rma/raw.dat", x = "x", y = "y", log = FALSE, k = 2),
  list(id = "extreme_tails", input = "rma/tails.dat", x = "x", y = "y", log = FALSE, k = 10)
)

log10_two_sided <- function(t, df) (log(2) + pt(abs(t), df, lower.tail = FALSE, log.p = TRUE)) / log(10)

results <- lapply(cases, function(case) {
  table <- if (grepl("\\.tsv$", case$input)) read.delim(case$input, check.names = FALSE, colClasses = "character")
           else read_past(case$input)
  x <- as.numeric(table[[case$x]]); y <- as.numeric(table[[case$y]])
  keep <- complete.cases(x, y); x <- x[keep]; y <- y[keep]
  ax <- if (case$log) log10(x) else x; ay <- if (case$log) log10(y) else y
  n <- length(ax); df <- n - 2
  fit <- sma(ay ~ ax, slope.test = case$k * sign(cor(ax, ay)), alpha = 0.05)
  g <- fit$groupsummary
  st <- fit$slopetest[[1]]
  r <- cor(ax, ay)
  r_rf <- cor(ay - case$k * ax, ay + case$k * ax)
  t_rf <- r_rf * sqrt(df) / sqrt(1 - r_rf^2)
  t_r <- r * sqrt(df) / sqrt(1 - r^2)
  list(id = case$id, input = case$input, x = case$x, y = case$y, transform = if (case$log) "log10" else "none",
       null_magnitude = case$k, confidence = 0.95, n = n,
       smatr = list(call = sprintf("sma(y ~ x, slope.test = %s * sign(cor(x, y)), alpha = 0.05) on %s pairs",
                                   case$k, if (case$log) "log10" else "raw"),
                    slope = g$Slope, slope_low = g$Slope_lowCI, slope_high = g$Slope_highCI, r2 = g$r2,
                    correlation_p = g$pval, slope_test_r = st$r, slope_test_p = st$p),
       base = list(r = r, r_rf = r_rf, t_rf = t_rf, t_r = t_r, df = df,
                   magnitude_log10_p = log10_two_sided(t_rf, df), direction_log10_p = log10_two_sided(t_r, df)))
})

record <- list(kind = "independent_rma_inference_reference", generator = "references/r/rma_inference_reference.R",
               generated_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"), r_version = R.version.string,
               platform = R.version$platform,
               packages = list(smatr = as.character(packageVersion("smatr")), jsonlite = as.character(packageVersion("jsonlite"))),
               rtol = 1e-10, atol = 1e-10,
               note = paste("smatr's slope interval is the sample-sign component; the API's magnitude interval is compared",
                            "with its absolute values. smatr's slope test uses 1 - pf(), so tails come from base R pt(log.p = TRUE)."),
               cases = results)
writeLines(toJSON(record, auto_unbox = TRUE, digits = NA, pretty = TRUE), "rma-inference-reference.json")
