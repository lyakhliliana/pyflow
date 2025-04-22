format:
	yapf --style .style.yapf -i -r ./src

activate:
	source venv/bin/activate

uninstall_cache:
	find . -type d -name "__pycache__" -exec rm -rf {} +


extract:
	python3 -B -m interfaces.cli.cli extract ./src -o tmp/results/version1
union:
	python3 -B -m interfaces.cli.cli union tmp/results/version1 code
visualize:
	python3 -B -m interfaces.cli.cli visualize tmp/results/version1/union
diff:
	python3 -B -m interfaces.cli.cli diff tmp/results/version1 union code