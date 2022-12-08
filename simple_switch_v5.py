import json

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import route
from ryu.app.wsgi import WSGIApplication
from ryu.lib import dpid as dpid_lib
from ryu.lib.dpid import dpid_to_str

myapp_name = 'simpleswitch'

class SimpleSwitch(app_manager.RyuApp):
    _CONTEXTS = {'wsgi': WSGIApplication}
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchController,
                      {myapp_name: self})

        # learn mac addresses on each port of each switch
        self.mac_to_port = {}
        self.segmentos = {}
        self.regras = []
        self.listaRegraAcessoPorHosteSegmento = []

    def add_flow(self, datapath, match, actions, priority=1000, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def delete_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        mod = parser.OFPFlowMod(datapath, command=ofproto.OFPFC_DELETE, match=match,
                                out_port=ofproto.OFPP_ANY,
                                out_group=ofproto.OFPG_ANY,
                                )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        
        msg = ev.msg
        dp = ev.msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        self.delete_flow(dp)
        match = parser.OFPMatch()
        
        self.logger.info("New switch connected %s", dpid_to_str(dp.id))
        
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER,
                                          ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, match, actions, priority=0)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src
        print("Origem: ", src)
        print("destino: ", dst)

        dpid = dp.id
        self.mac_to_port.setdefault(dpid, {})
        print("dpid: ", dpid)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofp.OFPP_FLOOD

        actions = [ofp_parser.OFPActionOutput(out_port)]

        print("Porta de saída: ", out_port)
        print("Porta entrada: ", in_port)

        # install a flow to avoid packet_in next time
        if out_port != ofp.OFPP_FLOOD:
            if dpid == 1 and out_port == 1:
                actions.insert(0, ofp_parser.OFPActionSetQueue(queue_id=1))
            elif dpid == 1 and out_port == 2:
                actions.insert(0, ofp_parser.OFPActionSetQueue(queue_id=2))
            elif dpid == 2 and out_port == 1:
                actions.insert(0, ofp_parser.OFPActionSetQueue(queue_id=3))
            elif dpid == 2 and out_port == 2:
                actions.insert(0, ofp_parser.OFPActionSetQueue(queue_id=4))

            match = ofp_parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofp.OFP_NO_BUFFER:
                self.add_flow(dp, match, actions, buffer_id=msg.buffer_id)
                return
            else:
                self.add_flow(dp, match, actions)

        data = None
        if msg.buffer_id == ofp.OFP_NO_BUFFER:
             data = msg.data

        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions, data = data)
        dp.send_msg(out)
    
    def criarSegmento(self, data):
        for k in data:
            if k in self.segmentos.keys():                
                for y in self.segmentos[k]:
                    if y not in data[k]:
                       self.segmentos[k].extend(data[k])

            else:
                self.segmentos[k] = data[k]
    
    def deletarSegmento(self, segmentoDel):
        self.segmentos.pop(segmentoDel,None)
         
    def deletarHostSegmento(self, segmentoDel, hostDel):
        self.segmentos[segmentoDel].remove(hostDel)
    
    def criarRegra(self, data):
        host1 = list(data)[0]
        host2 = list(data)[1]
        print("data: ", data)
        print("host1: ",host1)
        print("host2: ",host2)
        for regra in self.regras:
            if data[host1] == regra[host1] and data[host2] == regra[host2]:
                regra["acao"] = data["acao"]
                return
        self.regras.append(data)
        print("Self regras:", self.regras)

    def criaRegraAcessoPorHosteSegmento(self, data):
        print("CERTO1")
        print(self.listaRegraAcessoPorHosteSegmento)

        self.listaRegraAcessoPorHosteSegmento.append(data)
    
    
class SimpleSwitchController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(SimpleSwitchController, self).__init__(req, link, data, **config)
        self.simple_switch_app = data[myapp_name]
    
    

    @route(myapp_name, '/simpleswitch/mactable/{dpid}', methods=['GET'])
    def list_mac_table(self, req, **kwargs):
        dpid = dpid_lib.str_to_dpid(kwargs.get('dpid'))

        if dpid not in self.simple_switch_app.mac_to_port:
            return Response(status=404)

        mac_table = self.simple_switch_app.mac_to_port.get(dpid, {})
        body = json.dumps(mac_table)
        return Response(content_type='application/json', body=body)
        
    @route(myapp_name, '/nac/segmentos/', methods=['POST'])
    def criarSegmento(self, req, **kwargs):
        try:
           data = req.json           
        except ValueError as e:     
            return Response(content_type='application/json', body=json.dumps({"error": str(e)}), status=400)
        
        self.simple_switch_app.criarSegmento(data)
        body = json.dumps({"Resultado":"Segmento criado com sucesso"})
        return Response(content_type='application/json', body=body)
    
    @route(myapp_name, '/nac/segmentos/', methods=['GET'])
    def listarSegmentos(self, req, **kwargs):
        
        body = json.dumps(self.simple_switch_app.segmentos)
        return Response(content_type='application/json', body=body)

    @route(myapp_name, '/nac/segmentos/{segmento}', methods=['DELETE'])
    def deletarSegmento(self, req, **kwargs):
        segmentoDel = kwargs.get('segmento')
        print('id que ta entrando: ',segmentoDel)

        mensagem = {"Resultado":"Segmento "+segmentoDel+" deletado com sucesso"}

        self.simple_switch_app.deletarSegmento(segmentoDel)
        body = json.dumps(mensagem)
        return Response(content_type='application/json', body=body)

    @route(myapp_name, '/nac/segmentos/{segmento}/{host}', methods=['DELETE'])
    def deletarHostSegmento(self, req, **kwargs):
        segmentoDel = kwargs.get('segmento')
        hostDel = kwargs.get('host')
        print('segmentoDel: ',segmentoDel)
        print('hostDel: ',hostDel)

        self.simple_switch_app.deletarHostSegmento(segmentoDel, hostDel)
        body = json.dumps({"Resultado":"deletado com sucesso"})
        return Response(content_type='application/json', body=body)

    @route(myapp_name, '/nac/regras/', methods=['POST'])
    def criarRegra(self, req, **kwargs):
        try:
           data = req.json           
        except ValueError as e:     
            return Response(content_type='application/json', body=json.dumps({"error": str(e)}), status=400)

        self.simple_switch_app.criarRegra(data)
        body = json.dumps({"Resultado":"Regra criada com sucesso"})
        return Response(content_type='application/json', body=body)
    
    @route(myapp_name, '/nac/regras/', methods=['GET'])
    def listarRegras(self, req, **kwargs):
        
        body = json.dumps(self.simple_switch_app.regras)
        return Response(content_type='application/json', body=body)

    @route(myapp_name, '/nac/controle/', methods=['POST'])
    def criarRegra(self, req, **kwargs):
        try:
           data = req.json           
        except ValueError as e:     
            return Response(content_type='application/json', body=json.dumps({"error": str(e)}), status=400)
        print("data:",data.keys())
        if("host" in data.keys()):
            self.simple_switch_app.criaRegraAcessoPorHosteSegmento(data)#FALTA CRIAR ENDPOINT NO POSTMAN
        else:
            self.simple_switch_app.criarRegra(data)
        body = json.dumps({"Resultado":"Regra criada com sucesso"})
        return Response(content_type='application/json', body=body)

    @route(myapp_name, '/nac/controle/', methods=['GET'])
    def consultaRegras(self, req, **kwargs):


        body = json.dumps(self.simple_switch_app.regras)
        
        return Response(content_type='application/json', body=body)

    
    # @route(myapp_name, '/nac/controle/', methods=['POST'])
    # def criarRegraAcessoPorHosteSegmento(self, req, **kwargs):##fazer passo 6!!
    #     try:
    #        data = req.json           
    #     except ValueError as e:     
    #         return Response(content_type='application/json', body=json.dumps({"error": str(e)}), status=400)

    #     self.simple_switch_app.criaRegraAcessoPorHosteSegmento(data)
    #     body = json.dumps({"Resultado":"Regra criada com sucesso"})
    #     return Response(content_type='application/json', body=body)