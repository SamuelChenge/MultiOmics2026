# Makes one high-resolution PNG per figure used in the Study B slides, plus
# the key QC figures from 01-qc.qmd. Run it any time the underlying documents
# change:
#
#   Rscript group_project/make_slide_figures.R
#
# Output: group_project/slide_figures/*.png (300 dpi, ready for slides)

suppressPackageStartupMessages({
  library(tidyverse)
  library(here)
  library(DESeq2)
  library(microViz)
  library(phyloseq)
  library(vegan)
  library(patchwork)
  library(ggrepel)
})

source(here("R/count_tables.R"))

outdir <- here("group_project", "slide_figures")
dir.create(outdir, showWarnings = FALSE)

d  <- read_counts("group_b")
sp <- d$species
ge <- d$genes
md <- d$metadata |>
  mutate(arm_group = if_else(arm == "ring", "ring", "systemic"))

lacto_taxa <- d$taxonomy |> filter(Genus == "Lactobacillus") |> pull(taxon)
lacto_frac <- colSums(sp[lacto_taxa, , drop = FALSE]) / colSums(sp)
md$community <- ifelse(lacto_frac >= 0.5, "lactobacillus", "anaerobe")

save_png <- function(p, name, w, h) {
  ggsave(here("group_project", "slide_figures", name), p,
         width = w, height = h, dpi = 300, bg = "white")
  cat("wrote", name, "\n")
}

## ---- Ordinations (shared by Q1 / Q2 / Q3) ---------------------------------

ps_sp <- as_counts(dataset = "group_b", table = "microbiome", data = d)
sd <- as(sample_data(ps_sp), "data.frame")
sd$arm <- md$arm[match(sd$sample_id, md$sample_id)]
sd$community <- md$community[match(sd$sample_id, md$sample_id)]
sample_data(ps_sp) <- sample_data(sd)
ord_sp <- ps_sp |>
  tax_transform("clr", zero_replace = "halfmin") |>
  dist_calc("euclidean") |>
  ord_calc("PCoA")
eig_sp <- attr(ord_sp, "ord")$CA$eig
sh_sp  <- round(100 * eig_sp / sum(eig_sp), 1)

ps_genes <- as_counts(dataset = "group_b", table = "rnaseq",
                      min_count = 10, min_samples = 10, data = d)
sdg <- as(sample_data(ps_genes), "data.frame")
idx <- match(sdg$sample_id, md$sample_id)
sdg$arm       <- md$arm[idx]
sdg$arm_group <- md$arm_group[idx]
sdg$community <- md$community[idx]
sample_data(ps_genes) <- sample_data(sdg)
ord_g <- ps_genes |>
  tax_transform("clr", zero_replace = "halfmin") |>
  dist_calc("euclidean") |>
  ord_calc("PCoA")
eig_g <- attr(ord_g, "ord")$CA$eig
sh_g  <- round(100 * eig_g / sum(eig_g), 1)

## ---- Q1: species PCoA by arm ----------------------------------------------
p <- ord_plot(ord_sp, axes = 1:2, color = "arm") +
  stat_ellipse(aes(colour = arm), type = "norm", linewidth = 0.4) +
  labs(title = "Q1 — Species communities by method (PCoA, CLR + Euclidean)",
       x = sprintf("Axis 1 (%s%% of variation)", sh_sp[1]),
       y = sprintf("Axis 2 (%s%%)", sh_sp[2]), colour = "Arm")
save_png(p, "q1_species_pcoa_by_arm.png", 10, 5)

## ---- Q2: gene PCoA by arm --------------------------------------------------
p <- ord_plot(ord_g, axes = 1:2, color = "arm") +
  stat_ellipse(aes(colour = arm), type = "norm", linewidth = 0.4) +
  labs(title = "Q2 — Host gene expression by method (PCoA, CLR + Euclidean)",
       x = sprintf("Axis 1 (%s%% of variation)", sh_g[1]),
       y = sprintf("Axis 2 (%s%%)", sh_g[2]), colour = "Arm")
save_png(p, "q2_gene_pcoa_by_arm.png", 10, 5)

## ---- Q2: volcano, ring vs systemic ----------------------------------------
genes_f <- ge[rowSums(ge >= 10) >= 10, ]
rownames(md) <- md$sample_id
dds <- DESeq(DESeqDataSetFromMatrix(genes_f, md, design = ~ rnaseq_batch + arm_group),
             quiet = TRUE)
res_df <- as.data.frame(results(dds, contrast = c("arm_group", "ring", "systemic"))) |>
  rownames_to_column("ensembl_gene_id") |>
  left_join(d$gene_info |> select(ensembl_gene_id, symbol), by = "ensembl_gene_id") |>
  mutate(symbol = coalesce(symbol, ensembl_gene_id),
         padj   = replace_na(padj, 1))

p <- res_df |>
  mutate(hit  = padj < 0.05,
         label = if_else(rank(padj) <= 10, symbol, NA_character_)) |>
  ggplot(aes(log2FoldChange, -log10(padj), colour = hit)) +
  geom_point(size = 1, alpha = 0.6, show.legend = FALSE) +
  scale_colour_manual(values = c("grey70", "firebrick")) +
  geom_text_repel(aes(label = label), size = 2.8, max.overlaps = 20,
                  show.legend = FALSE) +
  labs(title = "Q2 — Ring vs systemic: 165 genes at FDR < 0.05 (n = 26 vs 67)",
       x = "log2 fold change (ring vs systemic)",
       y = "-log10 adjusted p-value")
save_png(p, "q2_volcano_ring_vs_systemic.png", 10, 5)

## ---- Q3: gene PCoA by community type --------------------------------------
p <- ord_plot(ord_g, axes = 1:2, color = "community") +
  stat_ellipse(aes(colour = community), type = "norm", linewidth = 0.4) +
  labs(title = "Q3 — Host gene expression by community type (same gene PCoA)",
       x = sprintf("Axis 1 (%s%% of variation)", sh_g[1]),
       y = sprintf("Axis 2 (%s%%)", sh_g[2]), colour = "Community")
save_png(p, "q3_gene_pcoa_by_community.png", 10, 5)

## ---- QC: library sizes ----------------------------------------------------
qc <- bind_cols(md, lib_species = colSums(sp), lib_genes = colSums(ge))
p <- bind_cols(
  md, lib_species = colSums(sp), lib_genes = colSums(ge)
) |>
  pivot_longer(c(lib_species, lib_genes), names_to = "table", values_to = "reads") |>
  ggplot(aes(reads)) +
  geom_histogram(bins = 30, fill = "grey70", colour = "white") +
  facet_wrap(~table, scales = "free") +
  labs(title = "QC — Sequencing depth per sample",
       x = "reads per sample", y = "samples")
save_png(p, "qc_library_sizes.png", 10, 5)

## ---- QC: haemoglobin (blood) signal ---------------------------------------
hb <- d$gene_info |> filter(symbol %in% c("HBB", "HBA1", "HBA2")) |> pull(ensembl_gene_id)
qc$hbb_share <- colSums(ge[hb, , drop = FALSE]) / qc$lib_genes
p <- ggplot(qc, aes(reorder(sample_id, hbb_share), hbb_share)) +
  geom_col(fill = "grey70") +
  scale_y_continuous(labels = scales::percent) +
  labs(title = "QC — Blood signal (HBB/HBA reads) per sample; B093 stands out",
       x = NULL, y = "share of all gene reads") +
  theme(axis.text.x = element_blank())
save_png(p, "qc_hbb_blood_signal.png", 10, 5)

## ---- QC: batch vs library size --------------------------------------------
p <- ggplot(qc, aes(rnaseq_batch, lib_genes, fill = arm)) +
  geom_boxplot() +
  scale_y_log10(labels = scales::comma) +
  labs(title = "QC — Gene library size by sequencing batch and arm",
       y = "reads (log10)", fill = "Arm", x = "Sequencing batch")
save_png(p, "qc_batch_library_size.png", 10, 5)

## ---- QC: feature prevalence ------------------------------------------------
prev_sp <- rowSums(sp > 0) / ncol(sp)
prev_ge <- rowSums(ge > 0) / ncol(ge)
p <- data.frame(prevalence = c(prev_sp, prev_ge),
                table = rep(c("species", "genes"),
                            c(length(prev_sp), length(prev_ge)))) |>
  ggplot(aes(prevalence, fill = table)) +
  geom_density(alpha = 0.5) +
  labs(title = "QC — In how many samples is each feature seen?",
       x = "fraction of samples with the feature present", y = NULL, fill = NULL)
save_png(p, "qc_feature_prevalence.png", 10, 5)

## ---- QC: species ordination three ways + scree -----------------------------
ord_bray    <- ps_sp |> tax_transform("identity") |> dist_calc("bray")    |> ord_calc("PCoA")
ord_jaccard <- ps_sp |> tax_transform("binary")   |> dist_calc("jaccard") |> ord_calc("PCoA")
plot_ord <- function(ord, name) {
  eig <- attr(ord, "ord")$CA$eig
  sh  <- round(100 * eig / sum(eig), 1)
  ord_plot(ord, axes = 1:2, color = "community") +
    labs(title = name, x = sprintf("Axis 1 (%s%%)", sh[1]),
         y = sprintf("Axis 2 (%s%%)", sh[2]))
}
scree <- bind_rows(
  lapply(list("Bray-Curtis" = ord_bray, "Jaccard" = ord_jaccard,
              "CLR + Euclidean" = ord_sp), function(ord) {
    eig <- attr(ord, "ord")$CA$eig[1:8]
    tibble(axis = seq_along(eig), share = eig / sum(eig))
  }) |> imap(~ mutate(.x, distance = .y))
)
p <- wrap_plots(
  plot_ord(ord_bray, "Bray-Curtis"),
  plot_ord(ord_jaccard, "Jaccard"),
  plot_ord(ord_sp, "CLR + Euclidean"),
  ncol = 3
) / ggplot(scree, aes(axis, share)) +
  geom_col(fill = "grey40") +
  facet_wrap(~ distance) +
  labs(title = "Scree: share of variation held by the first 8 axes",
       x = "Axis", y = "Share of variation") +
  theme_bw()
save_png(p, "qc_species_ordination_three_ways.png", 13, 6)

## ---- Confounder: vaginal pH by arm -----------------------------------------
p <- ggplot(md, aes(arm, ph, fill = arm)) +
  geom_boxplot(show.legend = FALSE, outlier.alpha = 0.4) +
  labs(title = "The one baseline imbalance: vaginal pH by method (Kruskal–Wallis p = 0.02)",
       x = NULL, y = "vaginal pH")
save_png(p, "confounder_ph_by_arm.png", 10, 5)

cat("all figures written to", outdir, "\n")
