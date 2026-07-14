## Summary

Describe the problem and the focused change.

## Capability level

- [ ] Guidance only
- [ ] Live partial
- [ ] Live end-to-end validated
- [ ] No capability claim changed

## Safety and compatibility

Describe credential, cost, IAM, networking, approval, cleanup, documentation, and
agent-compatibility effects. Do not include real account or resource data.

## Validation

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 -m compileall -q skills/byteplus-cloud/scripts`
- [ ] `python3 scripts/check_public_tree.py`
- [ ] Relevant offline regression added or updated
- [ ] Public validation matrix updated when the capability claim changed

## Official sources

Link the current official BytePlus or Agent Skills sources used for volatile
claims.
