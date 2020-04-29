# kibana-ops-toolkit

## Fix Kibana Index Migration Issue

https://github.com/opendistro-for-elasticsearch/security/issues/11
https://github.com/opendistro-for-elasticsearch/security/pull/17
https://github.com/opendistro-for-elasticsearch/security-kibana-plugin/issues/102

```
# run inspect
python fix-kibana-index-migration-issue

# run fix
python fix-kibana-index-migration-issue --action fix

# run against https://admin:admin@localhost:9200/
python fix-kibana-index-migration-issue --usessl --action fix
```


## Use https://www.graphviz.org/ to generate state transition diagram

* http://www.webgraphviz.com/

* Graphviz Preview (for VSCode)

* Install Graphviz on Mac OS X

```
brew install graphviz
```
