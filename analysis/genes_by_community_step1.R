# Exercise 1, Step 1 of notebooks/04-differential.qmd
# DESeq2 on the gene table at week 18, contrast: anaerobe vs lactobacillus.

library(tidyverse)
library(here)
library(DESeq2)

source(here("R/count_tables.R"))
d <- read_counts("instructional")

sample_groups <- read_csv(here("data/my_sample_groups.csv"))
metadata <- d$metadata |> left_join(sample_groups, by = "sample_id")

# 1. Keep only week 18 samples (one visit, so each participant appears once)
keep    <- metadata$time_point == "week_18"
meta18  <- metadata[keep, ]
genes18 <- d$genes[, meta18$sample_id, drop = FALSE]

# 2. CHECK THE SAMPLE ORDER: count columns must match metadata rows exactly.
stopifnot(identical(colnames(genes18), meta18$sample_id))
cat("SAMPLE ORDER OK:", ncol(genes18), "samples, columns == sample_id in order\n")
print(table(meta18$community))

# 3. Filter genes: at least 10 counts in at least a quarter of the samples
n18    <- ncol(genes18)
keep_g <- rowSums(genes18 >= 10) >= ceiling(n18 / 4)
genes_f <- genes18[keep_g, ]
cat("GENES TESTED:", nrow(genes_f), "of", n18, "\n")

# 4. Fix the contrast direction: reference level = lactobacillus,
#    so positive log2FoldChange means HIGHER in anaerobe.
meta18$community <- relevel(factor(meta18$community), ref = "lactobacillus")

dds <- DESeqDataSetFromMatrix(genes_f, meta18, design = ~ community)
dds <- DESeq(dds)
cat("RESULTS NAME:", resultsNames(dds), "\n")
res <- results(dds, contrast = c("community", "anaerobe", "lactobacillus"))
print(summary(res))

# 5. Sanity-check direction on a top hit: compare its raw mean counts
#    between the two groups by hand.
top <- rownames(res)[order(res$pvalue)][1]
tab <- tapply(as.numeric(genes_f[top, ]), meta18$community, mean)
cat("TOP GENE", top, "- mean raw counts per group:\n")
print(tab)
cat("log2FC from DESeq2:", res[top, "log2FoldChange"],
    "| naive log2 ratio:", log2(tab["anaerobe"] / tab["lactobacillus"]), "\n")

# 6. Attach gene info and save
out <- as.data.frame(res) |>
  rownames_to_column("feature") |>
  left_join(select(d$gene_info, ensembl_gene_id, symbol, gene_name),
            by = c("feature" = "ensembl_gene_id")) |>
  arrange(pvalue)

write_csv(out, here("data", "genes_by_community.csv"))
cat("SAVED:", nrow(out), "rows -> data/genes_by_community.csv\n")
