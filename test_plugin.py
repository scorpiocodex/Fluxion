from fluxion.plugins.manager import PluginManager

pm = PluginManager()
print("Plugins in JSON:", pm.list_plugins())

ipfs_plugin = pm.load("ipfs")
print("Loaded IPFS Plugin:", ipfs_plugin)
print("Is ProtocolPlugin?", type(ipfs_plugin).__bases__)

handler = pm.get_protocol_handler("ipfs")
print("Handler for 'ipfs':", handler)

for proto, plugin in pm._protocols.items():
    print(f"Protocol '{proto}' -> {plugin}")
