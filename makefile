# Push to main quicker

.PHONY: all add commit push

DATE := $(shell date +%Y-%m-%d)

all: add commit push

add:
	git add .

commit:
	@read -p "Please enter an additional commit message: " msg; \
	git commit -m "Updates $(DATE) - $$msg"

push:
	git push
