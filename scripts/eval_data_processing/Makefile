SCRIPTS := plotting/query.py \
	plotting/plotting.py \
	plotting/color.py \
	docker-image
SVG_TARGETS = charts/single_vs_multi_compressed.svg \
	charts/ablation_study_charts_remaining_compressed.svg \
	charts/ablation_study_charts_compressed.svg \
	charts/cve_cov_charts_compressed.svg
TARGETS = $(SVG_TARGETS) \
	/home/user/hoedur-experiments/01-bug-finding-ability/results/figure_5_cve_coverage_plot.pdf \
	/home/user/hoedur-experiments/02-coverage-est-data-set/results/figure_6_baseline_coverage_plot.pdf \
	/home/user/hoedur-experiments/02-coverage-est-data-set/results/figure_8_appendix_baseline_coverage_plot.pdf \
	/home/user/hoedur-experiments/03-advanced-mutations/results/figure_7_baseline_dict_coverage_plot.pdf \
	charts/ablation_study_charts.png \
	charts/cve_cov_charts.png \
	charts/single_vs_multi.png \
	charts/ablation_study_charts_remaining.png

.DEFAULT_GOAL := all
MAKEFLAGS := --jobs=$(shell nproc)

# For running the plotting environment
docker:
	@docker --version >/dev/null 2>&1 || (echo "ERROR: docker is required."; exit 1)

docker-image: docker
	bash ./env/build.sh

charts/cve_cov_charts.png: charts/cve_cov_charts.svg
	./env/run.sh inkscape --export-dpi 100 charts/cve_cov_charts.svg -o charts/cve_cov_charts.png

charts/cve_cov_charts.svg: $(SCRIPTS) plot_cve.py
	./env/run.sh python3 plot_cve.py charts/cve_cov_charts.svg

charts/cve_cov_charts_compressed.svg: charts/cve_cov_charts.svg
	./env/run.sh svgcleaner charts/cve_cov_charts.svg charts/cve_cov_charts_compressed.svg

/home/user/hoedur-experiments/01-bug-finding-ability/results/figure_5_cve_coverage_plot.pdf: charts/cve_cov_charts_compressed.svg
	./env/run.sh inkscape \
		--export-type=pdf \
		--export-filename=/home/user/hoedur-experiments/01-bug-finding-ability/results/figure_5_cve_coverage_plot.pdf \
		charts/cve_cov_charts_compressed.svg



charts/ablation_study_charts.png: charts/ablation_study_charts.svg
	./env/run.sh inkscape --export-dpi 100 charts/ablation_study_charts.svg -o charts/ablation_study_charts.png

charts/ablation_study_charts.svg: $(SCRIPTS) plot_ablation_study.py
	./env/run.sh python3 plot_ablation_study.py charts/ablation_study_charts.svg

charts/ablation_study_charts_compressed.svg: charts/ablation_study_charts.svg
	./env/run.sh svgcleaner charts/ablation_study_charts.svg charts/ablation_study_charts_compressed.svg

/home/user/hoedur-experiments/02-coverage-est-data-set/results/figure_6_baseline_coverage_plot.pdf: charts/ablation_study_charts_compressed.svg
	./env/run.sh inkscape \
		--export-type=pdf \
		--export-filename=/home/user/hoedur-experiments/02-coverage-est-data-set/results/figure_6_baseline_coverage_plot.pdf \
		--actions 'select-all:groups\;SelectionUnGroup\;' \
		charts/ablation_study_charts_compressed.svg




charts/ablation_study_charts_remaining.png: charts/ablation_study_charts_remaining.svg
	./env/run.sh inkscape --export-dpi 100 charts/ablation_study_charts_remaining.svg -o charts/ablation_study_charts_remaining.png

charts/ablation_study_charts_remaining.svg: $(SCRIPTS) plot_ablation_study_remaining.py
	./env/run.sh python3 plot_ablation_study_remaining.py charts/ablation_study_charts_remaining.svg

charts/ablation_study_charts_remaining_compressed.svg: charts/ablation_study_charts_remaining.svg
	./env/run.sh svgcleaner charts/ablation_study_charts_remaining.svg charts/ablation_study_charts_remaining_compressed.svg

/home/user/hoedur-experiments/02-coverage-est-data-set/results/figure_8_appendix_baseline_coverage_plot.pdf: charts/ablation_study_charts_remaining_compressed.svg
	./env/run.sh inkscape \
		--export-type=pdf \
		--export-filename=/home/user/hoedur-experiments/02-coverage-est-data-set/results/figure_8_appendix_baseline_coverage_plot.pdf \
		--actions 'select-all:groups\;SelectionUnGroup\;' \
		charts/ablation_study_charts_remaining_compressed.svg




charts/single_vs_multi.png: charts/single_vs_multi.svg
	./env/run.sh inkscape --export-dpi 100 charts/single_vs_multi.svg -o charts/single_vs_multi.png

charts/single_vs_multi.svg: $(SCRIPTS) plot_single_vs_multi.py
	./env/run.sh python3 plot_single_vs_multi.py charts/single_vs_multi.svg

charts/single_vs_multi_compressed.svg: charts/single_vs_multi.svg
	./env/run.sh svgcleaner charts/single_vs_multi.svg charts/single_vs_multi_compressed.svg

/home/user/hoedur-experiments/03-advanced-mutations/results/figure_7_baseline_dict_coverage_plot.pdf: charts/single_vs_multi_compressed.svg
	./env/run.sh inkscape \
		--export-type=pdf \
		--export-filename=/home/user/hoedur-experiments/03-advanced-mutations/results/figure_7_baseline_dict_coverage_plot.pdf \
		charts/single_vs_multi_compressed.svg

# Build SVG + PDF + PNG
all: docker-image $(TARGETS)

# Build only SVG
svg: docker-image $(SVG_TARGETS)

clean:
	rm -f charts/*.{png,svg,pdf}
