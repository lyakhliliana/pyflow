format:
	yapf --style .style.yapf -i -r ./src

activate:
	source venv/bin/activate

clean_cache:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

test:
	python3 -B -m pytest tests/ -v
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

git_example:
	python3 -B -m interfaces.cli.cli extract ./src -o tmp/results/version1 -l https://github.com/aedobrynin/whiteboard-v2.git
	python3 -B -m interfaces.cli.cli visualize tmp/results/version1/code

extract:
	pyflow extract ./src tmp/results/version1/code
	pyflow visualize tmp/results/version1/code
	find . -type d -name "__pycache__" -exec rm -rf {} +

init_additional:
	pyflow init_additional tmp/results/add
	find . -type d -name "__pycache__" -exec rm -rf {} +

union:
	pyflow union tmp/results/version1/code tmp/results/add tmp/results/version1/union
	find . -type d -name "__pycache__" -exec rm -rf {} +

visualize:
	pyflow visualize tmp/results/version1/union
	find . -type d -name "__pycache__" -exec rm -rf {} +

diff:
	pyflow diff tmp/results/version1/code tmp/results/version2/code tmp/results/difference
	pyflow visualize -m diff tmp/results/difference
	find . -type d -name "__pycache__" -exec rm -rf {} +

contract:
	pyflow contract tmp/results/version1/union tmp/results/version1/contract extract
	find . -type d -name "__pycache__" -exec rm -rf {} +

filter:
	pyflow filter tmp/results/version1/contract tmp/results/version1/filter --node-types class func body arc_elem use_case
	find . -type d -name "__pycache__" -exec rm -rf {} +

get_used:
	pyflow get_used tmp/results/version1/union tmp/results/version1/get_used interfaces/cli/cli.py#main
	find . -type d -name "__pycache__" -exec rm -rf {} +

get_dependent:
	pyflow get_dependent tmp/results/version1/union tmp/results/version1/get_dependent core/models/node.py#Node
	find . -type d -name "__pycache__" -exec rm -rf {} +