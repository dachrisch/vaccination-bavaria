from connectors import UsernamePasswordLoginProvider, ImpzentrenBayerConnector


class WithConnector:
    connector = ImpzentrenBayerConnector(UsernamePasswordLoginProvider())
