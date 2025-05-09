format:
	yapf --style .style.yapf -i -r ./src

activate:
	source venv/bin/activate

uninstall_cache:
	find . -type d -name "__pycache__" -exec rm -rf {} +

git_example:
	python3 -B -m interfaces.cli.cli extract ./src -o tmp/results/version1 -l https://github.com/aedobrynin/whiteboard-v2.git
	python3 -B -m interfaces.cli.cli visualize tmp/results/version1/code
extract:
	python3 -B -m interfaces.cli.cli extract ./src -o tmp/results/version1
union:
	python3 -B -m interfaces.cli.cli union tmp/results/version1 code
visualize:
	python3 -B -m interfaces.cli.cli visualize tmp/results/version1/union
diff:
	python3 -B -m interfaces.cli.cli diff tmp/results/version1/code tmp/results/version2/code tmp/results/difference
	python3 -B -m interfaces.cli.cli visualize -m diff tmp/results/difference