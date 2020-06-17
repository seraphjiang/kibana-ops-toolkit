import argparse
import sys

from elasticsearch import Elasticsearch

# es = Elasticsearch([{
#     "host": "localhost",
#     "port": "9200",
#     "use_ssl": False
# }])

class FixKibanaIndexMigrationIssue:
    def __init__(self, es):
        self.es = es
        self.kibana_indices_aliases = self.es.indices.get_alias(".kibana*")

    def find_end(self, source):
        val = -1
        for _ in range(0, 3):
            val = source.find('_', val + 1)
        return val


    def restore_alias(self, kibana_index_name, last_kibana_index_name):
        self.es.indices.update_aliases({
            "actions": [
                {"add":    {"index": last_kibana_index_name, "alias": kibana_index_name}},
                {"remove_index": {"index": kibana_index_name}}
            ]
        })
        print(kibana_index_name, last_kibana_index_name, 'fixed')

    def reindex_remove(self, kibana_index_name):
        self.es.reindex({
            "source": {
                "index": kibana_index_name
            },
            "dest": {
                "index": kibana_index_name + "_1"
            }
        })
        print("reindex from ", kibana_index_name, ' to ', kibana_index_name + "_1")
        self.es.indices.delete(kibana_index_name, timeout='10s')
        print("deleted ", kibana_index_name)

    def get_kibana_indices_and_aliases(self):
        return self.es.indices.get_alias(".kibana*")


    def scan_classify(self):
        reduce = {}

        for key in sorted(self.kibana_indices_aliases.keys()):
            pos = self.find_end(key)
            kibana_index_name = key[0: pos]
            kibana_index_name_version = int(key[pos+1:]) if (pos > 0) else 0
            if (kibana_index_name not in reduce):
                reduce[kibana_index_name] = {
                    'max_kibana_version': 0, 'last_kibana_name': key}
            reduce[kibana_index_name][key] = kibana_index_name_version

            if(kibana_index_name_version > reduce[kibana_index_name]['max_kibana_version']):
                reduce[kibana_index_name]['max_kibana_version'] = kibana_index_name_version
                reduce[kibana_index_name]['last_kibana_name'] = key
        return reduce

    def inspect(self):
        reduce = self.scan_classify()
        for key in sorted(reduce.keys()):
            if(len(reduce[key]) > 3):
                last_kibana_name = reduce[key]['last_kibana_name']
                if ('aliases' in self.kibana_indices_aliases[last_kibana_name] and self.kibana_indices_aliases[last_kibana_name]['aliases'] == {}):
                    if(key in self.kibana_indices_aliases):
                        print(key, last_kibana_name, 'missing alias, need to fix')
                    else:
                        print(key, last_kibana_name, 'cannot find kibana index. ignore')
            else:
                idx_info = reduce[key];
                if (idx_info["max_kibana_version"] != idx_info[idx_info["last_kibana_name"]]):
                    # .kibana {'max_kibana_version': 1, 'last_kibana_name': '.kibana_1', '.kibana_1': 1} only one .kbana index, will create alias
                    print(key,reduce[key], 'only one .kbana index, will create alias')
                #else:
                    # print(reduce[key]["last_kibana_name"], 'only one index, no need to fix')


    def list(self):
        reduce = self.scan_classify()
        for key in sorted(reduce.keys()):
            if(len(reduce[key]) > 3):
                last_kibana_name = reduce[key]['last_kibana_name']
                if ('aliases' in self.kibana_indices_aliases[last_kibana_name] and self.kibana_indices_aliases[last_kibana_name]['aliases'] == {}):
                    if(key in self.kibana_indices_aliases):
                        print(key, last_kibana_name, 'missing alias, need to fix')
                    else:
                        print(key, last_kibana_name, 'cannot find kibana index. ignore')
            else:
                print(key)

    def reindex(self):
        reduce = self.scan_classify()
        for key in sorted(reduce.keys()):
            # no alias, only one bad index
            if(len(reduce[key]) == 3 and reduce[key]["max_kibana_version"] == 0):
                print(reduce[key])
                print(key)
                self.reindex_remove(reduce[key]["last_kibana_name"])
                

    def fix(self):
        reduce = self.scan_classify()

        for key in sorted(reduce.keys()):
            if(len(reduce[key]) > 3):
                last_kibana_name = reduce[key]['last_kibana_name']
                # print(key, last_kibana_name, kibana_indices_aliases[last_kibana_name])
                if ('aliases' in self.kibana_indices_aliases[last_kibana_name] and self.kibana_indices_aliases[last_kibana_name]['aliases'] == {}):
                    if (key in self.kibana_indices_aliases):
                        # print(last_kibana_name, kibana_indices_aliases[last_kibana_name], 'bad', len(reduce[key]) -3)
                        print(key, last_kibana_name, 'bad')
                        self.restore_alias(key, last_kibana_name)

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action", help="action to .kibana* index. e.g. inspect, fix", default="inspect")

    parser.add_argument(
        "--host", help="elasticsearch host", default="localhost")
    parser.add_argument(
        "--port", help="http port", default="9200")
    parser.add_argument(
        "--usessl", help="use https", type=bool, default=False)
    parser.add_argument(
        "--user", help="user name", default="admin")             
    parser.add_argument(
        "--secret", help="user secret", default="admin")             

    args = parser.parse_args()
    print(args)
    esconfig = {
        "host": args.host,
        "port": args.port,
        "use_ssl": args.usessl
    }
    
    if (args.usessl):
        esconfig["verify_certs"] = False
        esconfig["http_auth"] = (args.user, args.secret)

    es = Elasticsearch([esconfig])

    print(esconfig)
    tool = FixKibanaIndexMigrationIssue(es)
    if (args.action == "fix"):
        tool.fix()
    elif (args.action == "list"):
        tool.list()
    elif (args.action == "reindex"):
        tool.reindex()        
    else:
        tool.inspect()


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print('fix-kibana-index-migration-issue interrupted by user, exiting')
        sys.exit(0)
