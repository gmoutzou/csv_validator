#
# project: CSV Validator
#
# configuration
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#


from configparser import ConfigParser


def load_config(filename='config.ini', section='csv'):
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to csv
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return config

def write_config(filename='config.ini', section='csv', config={}):
    parser = ConfigParser()
    parser.read(filename)
    parser[section] = config
    with open(filename, 'w') as configfile:
        parser.write(configfile)

def get_connection_string(config=load_config(section='postgresql')):
    pg_con_str = ''
    if config:
        pg_con_str = ('postgresql://' + 
                        config['user'] + ':' + 
                        config['password'] + '@' + 
                        config['host'] + ':' + 
                        config['port'] + '/' + 
                        config['dbname'])
    return pg_con_str

if __name__ == '__main__':
    config = load_config()
    print(config)
    