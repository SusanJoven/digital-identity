"""
Identidad Digital basada en Blockchain para Instituciones Educativas (v1.0) con Hyperledger Indy (v1.15.0)
Creación de identidad digital para miembros de la Universidad de los Andes (2020)

"""

import logging
import json
import argparse
import time
import sys
import zlib

"""
Imported modules: indy, indy and os
"""

from indy import pool, wallet, did, ledger, anoncreds, blob_storage
from src.utils import get_pool_genesis_txn_path, PROTOCOL_VERSION
from indy.error import ErrorCode, IndyError
from os.path import dirname


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  

user = {}
type_of_service = -1
type_of_user = -1
type_of_event = -1



async def run():

    """
    Student/User setup
    The user enter data as name, last name, identificacion and type of service  
    """

    logger.info("------------------------------")
    logger.info("== Student/User setup ==")
    logger.info("------------------------------")    

    global type_of_service
    global type_of_user
    global type_of_event
    name = input("Name:") 
    user['name'] = name
    last_name = input("Last Name:")
    user['last_name']=last_name
    print("Type of user: ")
    print("1. Student ")
    print("2. Teacher ")
    print("3. Employee")
    print("4. Invited")
    type_of_user = int(input("Enter the number for your type of user: "))
    if type_of_user == 1:
        status='student'
        user['status']=status
        id = input("ID:")
        user['id'] = id
        print("Type of service: ")
        print("1. Sicua ")
        print("2. Campus ")
        type_of_service= int(input("Enter the number for your type of service: "))
        if type_of_service == 1:
            await start()
        elif type_of_service == 2: 
            await start()
        else:
            print("Enter a valid number")     
    elif type_of_user == 2:
        status = 'teacher'
        user['status']=status
        id = input("ID:")
        user['id'] = id
        print("Type of service: ")
        print("1. Sicua ")
        print("2. Campus ")
        type_of_service = int(input("Enter the number for your type of service: "))
        if type_of_service == 1:
            await start()
        elif type_of_service == 2: 
            await start()
        else:
            print("Enter a valid number")  
    elif type_of_user == 3:
        status = 'employee'
        user['status']=status
        id = input("ID:")
        user['id'] = id
        type_of_service = 2
        await start()   
    elif type_of_user == 4:
        status = 'invited'
        user['status']=status
        id = input("ID:")
        user['id'] = id
        type_of_service = 2
        print("Type of event")
        print("1. Event #1 ")
        print("2. Event #2 ")
        type_of_event = int(input("Enter the number for your type of event: ")) 
        await start()


    else: 
        print("Enter a valid number")  
    

async def start():  

    """
    Indy nodes pool setup using the API pool provided by Hyperledger Indy
    """

    logger.info("===== Start =====")
    pool_ = {'name': 'pool1'}
    logger.info("Open Pool Ledger: {}".format(pool_['name']))
    pool_['genesis_txn_path'] = get_pool_genesis_txn_path(pool_['name'])
    pool_['config'] = json.dumps({"genesis_txn": str(pool_['genesis_txn_path'])})

    # Set protocol version 2 to work with Indy Node 1.4
    await pool.set_protocol_version(PROTOCOL_VERSION)

    """
    Creation of Indy nodes pool using the API pool provided by Hyperledger Indy
    """
    try:
        await pool.create_pool_ledger_config(pool_['name'], pool_['config'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    pool_['handle'] = await pool.open_pool_ledger(pool_['name'], None)

    logger.info("==============================")
    logger.info("=== Getting Trust Anchor credentials for Uniandes, Entry and Sicua  ==")
    logger.info("------------------------------")

    """
    Creation of Indy nodes: steward, uniandes, entry, sicua, user
    """

    steward = {
        'name': "Sovrin Steward",
        'wallet_config': json.dumps({'id': 'sovrin_steward_wallet'}),
        'wallet_credentials': json.dumps({'key': 'steward_wallet_key'}),
        'pool': pool_['handle'],
        'seed': '000000000000000000000000Steward1'
    }

    """
    Creation of wallet for steward using the API did provided by Hyperledger Indy
    """
    await create_wallet(steward)

    logger.info("\"Sovrin Steward\" -> Create and store in Wallet DID from seed")
    steward['did_info'] = json.dumps({'seed': steward['seed']})
    steward['did'], steward['key'] = await did.create_and_store_my_did(steward['wallet'], steward['did_info'])

    logger.info("==============================")
    logger.info("== Getting Trust Anchor credentials - Uniandes getting Verinym  ==")
    logger.info("------------------------------")
     
    uniandes = {
        'name': 'Uniandes',
        'wallet_config': json.dumps({'id': 'uniandes_wallet'}),
        'wallet_credentials': json.dumps({'key': 'uniandes_wallet_key'}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }

    """
    Creation of wallet for steward using the API did provided by Hyperledger Indy
    """

    await getting_verinym(steward, uniandes)

    logger.info("==============================")
    logger.info("== Getting Trust Anchor credentials - Entry getting Verinym  ==")
    logger.info("------------------------------")

    entry = {
        'name': 'Entry',
        'wallet_config': json.dumps({'id': 'entry_wallet'}),
        'wallet_credentials': json.dumps({'key': 'entry_wallet_key'}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }

    """
    Creation of wallet for entry using the API did provided by Hyperledger Indy
    """
    await getting_verinym(steward, entry)

    logger.info("==============================")
    logger.info("== Getting Trust Anchor credentials - Sicua getting Verinym  ==")
    logger.info("------------------------------")

    sicua = {
        'name': 'Sicua',
        'wallet_config': json.dumps({'id': 'sicua_wallet'}),
        'wallet_credentials': json.dumps({'key': 'sicua_wallet_key'}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }

    """
    Creation of wallet for sicua using the API did provided by Hyperledger Indy
    """
    await getting_verinym(steward, sicua)


    print("First name: " + user['name'])
    print("Last name: " + user['last_name'])
    print("User: "+ user['status'])
    print("ID: "+ user['id'])

    user['wallet_config'] = json.dumps({'id': user['name'].lower() +'_wallet'})
    user['wallet_credentials']= json.dumps({'key': user['name'].lower() +'_wallet_key'})
    user['pool'] = pool_['handle']

    """
    Creation of wallet for user using the API did provided by Hyperledger Indy
    """
    await create_wallet(user)

    (user['did'], user['key']) = await did.create_and_store_my_did(user['wallet'], "{}")

    logger.info("==============================")
    logger.info("=== Credential Schemas Setup ==")
    logger.info("------------------------------")

    logger.info("\"Uniandes\" -> Create \"Uniandino\" Schema")

    """
    Creation of the schema named Uniandino using the API anoncreds provided by Hyperledger Indy
    """
    uniandino = {
        'name': 'Uniandino',
        'version': '0.1',
        'attributes': ['first_name', 'last_name', 'status', 'id']
    }
    (uniandes['uniandino_schema_id'], uniandes['uniandino_schema']) = \
        await anoncreds.issuer_create_schema(uniandes['did'],    uniandino['name'],    uniandino['version'],
                                             json.dumps(uniandino['attributes']))
    uniandino_schema_id = uniandes['uniandino_schema_id']

    logger.info("\"Uniandes\" -> Send \"Uniandino\" Schema to Ledger")
    await send_schema(uniandes['pool'], uniandes['wallet'], uniandes['did'], uniandes['uniandino_schema'])

    time.sleep(1)  # sleep 1 second before getting schema
    

    logger.info("==============================")
    logger.info("=== Uniandes Credential Definition Setup ==")
    logger.info("------------------------------")

    logger.info("\"Uniandes\" -> Get from Ledger \"Uniandino\" Schema")
    (uniandes['uniandino_schema_id'], uniandes['uniandino_schema']) = \
        await get_schema(uniandes['pool'], uniandes['did'], uniandino_schema_id)
    
    logger.info("\"Uniandes\" -> Create and store in Wallet \"Uniandino\" Credential Definition")
    uniandino_cred_def = {
        'tag': 'TAG1',
        'type': 'CL',
        'config': {"support_revocation": True}
    }
    (uniandes['uniandino_cred_def_id'], uniandes['uniandino_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(uniandes['wallet'], uniandes['did'],
                                                               uniandes['uniandino_schema'],
                                                               uniandino_cred_def['tag'],
                                                               uniandino_cred_def['type'],
                                                               json.dumps(uniandino_cred_def['config']))

    logger.info("\"Uniandes\" -> Send \"Uniandino\" Credential Definition to Ledger")
    await send_cred_def(uniandes['pool'], uniandes['wallet'], uniandes['did'], uniandes['uniandino_cred_def'])

    """
    Creation of the Revocation Registry using the API anoncreds provided by Hyperledger Indy
    """
    
    logger.info("\"Uniandes\" -> Creates Revocation Registry")
    uniandes['tails_writer_config'] = json.dumps({'base_dir': "/tmp/indy_acme_tails", 'uri_pattern': ''})
    tails_writer = await blob_storage.open_writer('default', uniandes['tails_writer_config'])
    (uniandes['revoc_reg_id'], uniandes['revoc_reg_def'], uniandes['revoc_reg_entry']) = \
        await anoncreds.issuer_create_and_store_revoc_reg(uniandes['wallet'], uniandes['did'], 'CL_ACCUM', 'TAG1',
                                                          uniandes['uniandino_cred_def_id'],
                                                          json.dumps({'max_cred_num': 5,
                                                                      'issuance_type': 'ISSUANCE_ON_DEMAND'}),
                                                          tails_writer)

    logger.info("\"Uniandes\" -> Post Revocation Registry Definition to Ledger")
    uniandes['revoc_reg_def_request'] = await ledger.build_revoc_reg_def_request(uniandes['did'], uniandes['revoc_reg_def'])
    await ledger.sign_and_submit_request(uniandes['pool'], uniandes['wallet'], uniandes['did'], uniandes['revoc_reg_def_request'])

    logger.info("\"Uniandes\" -> Post Revocation Registry Entry to Ledger")
    uniandes['revoc_reg_entry_request'] = \
        await ledger.build_revoc_reg_entry_request(uniandes['did'], uniandes['revoc_reg_id'], 'CL_ACCUM',
                                                   uniandes['revoc_reg_entry'])
    await ledger.sign_and_submit_request(uniandes['pool'], uniandes['wallet'], uniandes['did'], uniandes['revoc_reg_entry_request'])

    logger.info("==============================")
    logger.info("=== Getting Uniandino with Uniandes ==")
    logger.info("==============================")
    

    logger.info("==============================")
    logger.info("== Getting Uniandino with Uniandes - Getting Uniandino Credential ==")
    logger.info("------------------------------")
    

    logger.info("\"Uniandes\" -> Create \"Uniandino\" Credential Offer for"+ user['name'])
    uniandes['uniandino_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(uniandes['wallet'], uniandes['uniandino_cred_def_id'])

    logger.info("\"Uniandes\" -> Send \"Uniandino\" Credential Offer to " + user['name'])
    user['uniandino_cred_offer'] = uniandes['uniandino_cred_offer']

    uniandino_cred_offer_object = json.loads(user['uniandino_cred_offer'])

    logger.info("\""+user['name']+ "\" -> Create and store " + user['name']+" Master Secret in Wallet")
    user['master_secret_id'] = await anoncreds.prover_create_master_secret(user['wallet'], None)

    logger.info("\""+user['name']+ "\"-> Get \"Uniandes Uniandino\" Credential Definition from Ledger")
    (user['uniandes_uniandino_cred_def_id'], user['uniandes_uniandino_cred_def']) = \
        await get_cred_def(user['pool'], user['did'], uniandino_cred_offer_object['cred_def_id'])

    logger.info("\""+user['name']+ "\" -> Create \"Uniandino\" Credential Request for Uniandes")
    (user['uniandino_cred_request'], user['uniandino_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(user['wallet'], user['did'],
                                                     user['uniandino_cred_offer'], user['uniandes_uniandino_cred_def'],
                                                     user['master_secret_id'])

    logger.info("\""+user['name']+ "\" -> Send \"Uniandino\" Credential Request to Uniandes")
       
    
    user['uniandino_cred_values'] = json.dumps({
        "first_name": {"raw": user['name'], "encoded": '1243969699234'},
        "last_name": {"raw": user['last_name'], "encoded": '14797928094'},
        "status": {"raw": user['status'], "encoded":'9836401234354351' },
        "id": {"raw": user['id'], "encoded": '92796994819'}  
    })
     
    uniandes['uniandino_cred_request'] = user['uniandino_cred_request']
    uniandes['uniandino_cred_values'] = user['uniandino_cred_values']


    logger.info("\"Uniandes\" -> Create \"Uniandino\" Credential for "+ user['name'])

    uniandes['blob_storage_reader_cfg_handle'] = await blob_storage.open_reader('default', uniandes['tails_writer_config'])
    print( uniandes['blob_storage_reader_cfg_handle'])
    uniandes['uniandino_cred'], uniandes['uniandino_cred_rev_id'], uniandes['user_cert_rev_reg_delta'] = \
        await anoncreds.issuer_create_credential(uniandes['wallet'], uniandes['uniandino_cred_offer'],
                                                 uniandes['uniandino_cred_request'],
                                                 uniandes['uniandino_cred_values'], uniandes['revoc_reg_id'],
                                                 uniandes['blob_storage_reader_cfg_handle'])

    logger.info("\"Uniandes\" -> Post Revocation Registry Delta to Ledger")
    uniandes['revoc_reg_entry_req'] = \
        await ledger.build_revoc_reg_entry_request(uniandes['did'], uniandes['revoc_reg_id'], 'CL_ACCUM',
                                                   uniandes['user_cert_rev_reg_delta'])
    await ledger.sign_and_submit_request(uniandes['pool'], uniandes['wallet'], uniandes['did'], uniandes['revoc_reg_entry_req'])

    logger.info("\"Uniandes\" -> Send \"Uniandino\" Credential to "+ user['name'])
    user['uniandino_cred'] = uniandes['uniandino_cred']
    uniandino_cred_object = json.loads(user['uniandino_cred'])
    
    logger.info("\""+user['name']+ "\"-> Gets RevocationRegistryDefinition for \"Uniandino\" Credential from Uniandes")
    user['uniandes_revoc_reg_des_req'] = \
        await ledger.build_get_revoc_reg_def_request(user['did'],
                                                     uniandino_cred_object['rev_reg_id'])
    user['uniandes_revoc_reg_des_resp'] = \
        await ensure_previous_request_applied(user['pool'], user['uniandes_revoc_reg_des_req'],
                                              lambda response: response['result']['data'] is not None)
    (user['uniandes_revoc_reg_def_id'], user['uniandes_revoc_reg_def_json']) = \
        await ledger.parse_get_revoc_reg_def_response(user['uniandes_revoc_reg_des_resp'])

    logger.info("\""+user['name']+ "\" -> Store \"Uniandino\" Credential from Uniandes")
    await anoncreds.prover_store_credential(user['wallet'], None, user['uniandino_cred_request_metadata'],
                                            user['uniandino_cred'],
                                            user['uniandes_uniandino_cred_def'], user['uniandes_revoc_reg_def_json'])
  
    """
    Proves the Uniandino credential provided by the user. 
    If the attributes of the credential are proved and the credential has not been revoked, the credential is accepted
    """
    async def get_into():

        logger.info("==============================")
        logger.info("== Trying to get into the university  with Entry - Uniandino proving ==")
        logger.info("------------------------------")

        logger.info("\"Entry\" -> Create \"Uniandino\" Proof Request")
        nonce = await anoncreds.generate_nonce()
        entry['uniandino_proof_request'] = json.dumps({
            'nonce': nonce,
            'name': 'Uniandino',
            'version': '0.1',
            'self_attested_attributes': {},
            'requested_attributes': {
                'attr1_referent': {
                    'name': 'first_name',
                    'restrictions': [{'cred_def_id': uniandes['uniandino_cred_def_id']}]
                },
                'attr2_referent': {
                    'name': 'last_name',
                    'restrictions': [{'cred_def_id': uniandes['uniandino_cred_def_id']}]
                },
                'attr3_referent': {
                    'name': 'id',
                    'restrictions': [{'cred_def_id': uniandes['uniandino_cred_def_id']}]
                }, 
                'attr4_referent': {
                    'name': 'status',
                    'restrictions': [{'cred_def_id': uniandes['uniandino_cred_def_id']}]
                }
                
            },
            'requested_predicates':{},
            'non_revoked': {'to': int(time.time())}
        
        })

        logger.info("\"Entry\" -> Send \"Uniandino\" Proof Request to "+ user['name'])
        user['uniandino_proof_request'] = entry['uniandino_proof_request']


        logger.info("\""+user['name']+ "\" -> Get credentials for \"Uniandino\" Proof Request")

        search_for_uniandino_proof_request = \
            await anoncreds.prover_search_credentials_for_proof_req(user['wallet'],
                                                                    user['uniandino_proof_request'], None)

        cred_for_attr1 = await get_credential_for_referent(search_for_uniandino_proof_request, 'attr1_referent')
        cred_for_attr2 = await get_credential_for_referent(search_for_uniandino_proof_request, 'attr2_referent')
        cred_for_attr3 = await get_credential_for_referent(search_for_uniandino_proof_request, 'attr3_referent')
        cred_for_attr4 = await get_credential_for_referent(search_for_uniandino_proof_request, 'attr4_referent')
        
        await anoncreds.prover_close_credentials_search_for_proof_req(search_for_uniandino_proof_request)
        user['creds_for_uniandino_proof'] = {cred_for_attr1['referent']: cred_for_attr1,
                                                cred_for_attr2['referent']: cred_for_attr2,
                                                cred_for_attr3['referent']: cred_for_attr3,
                                                cred_for_attr4['referent']: cred_for_attr4}
                            
        requested_timestamp = int(json.loads(entry['uniandino_proof_request'])['non_revoked']['to'])
    
       
        user['schemas_for_uniandino'], user['cred_defs_for_uniandino'], \
        user['revoc_states_for_uniandino'] = \
            await prover_get_entities_from_ledger(user['pool'], user['did'],
                                                user['creds_for_uniandino_proof'], user['name'], None, requested_timestamp)

        logger.info("\""+user['name']+ "\" -> Create \"Uniandino\" Proof")

        revoc_states_for_uniandino = json.loads(user['revoc_states_for_uniandino'])
        timestamp_for_attr1 = get_timestamp_for_attribute(cred_for_attr1, revoc_states_for_uniandino)
        timestamp_for_attr2 = get_timestamp_for_attribute(cred_for_attr2, revoc_states_for_uniandino)
        timestamp_for_attr3 = get_timestamp_for_attribute(cred_for_attr3, revoc_states_for_uniandino)
        timestamp_for_attr4 = get_timestamp_for_attribute(cred_for_attr4, revoc_states_for_uniandino)
        
        user['uniandino_requested_creds'] = json.dumps({
            'self_attested_attributes': {},
            'requested_attributes': {
                'attr1_referent': {'cred_id': cred_for_attr1['referent'], 'revealed': True, 'timestamp': timestamp_for_attr1},
                'attr2_referent': {'cred_id': cred_for_attr2['referent'], 'revealed': True, 'timestamp': timestamp_for_attr2},
                'attr3_referent': {'cred_id': cred_for_attr3['referent'], 'revealed': True, 'timestamp': timestamp_for_attr3},
                'attr4_referent': {'cred_id': cred_for_attr4['referent'], 'revealed': True, 'timestamp': timestamp_for_attr4}
            },
            'requested_predicates':{}
        })
        
        user['uniandino_proof'] = \
            await anoncreds.prover_create_proof(user['wallet'], user['uniandino_proof_request'],
                                                user['uniandino_requested_creds'], user['master_secret_id'],
                                                user['schemas_for_uniandino'],
                                                user['cred_defs_for_uniandino'],
                                                user['revoc_states_for_uniandino'])

        logger.info("\""+user['name']+ "\" -> Send \"Uniandino\" Proof to Entry")
        entry['uniandino_proof'] = user['uniandino_proof']

        uniandino_proof_object = json.loads(entry['uniandino_proof'])

        logger.info("\"Entry\" -> Get Schemas, Credential Definitions and Revocation Registries from Ledger"
                        " required for Proof verifying")

        entry['schemas_for_uniandino'], entry['cred_defs_for_uniandino'], \
        entry['revoc_ref_defs_for_uniandino'], entry['revoc_regs_for_uniandino'] = \
            await verifier_get_entities_from_ledger(entry['pool'], entry['did'],
                                                    uniandino_proof_object['identifiers'], entry['name'], requested_timestamp)

        logger.info("\"Entry\" -> Verify \"Uniandino\" Proof from "+ user['name'])

        print( uniandino_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw'])
        print(uniandino_proof_object['requested_proof']['revealed_attrs']['attr3_referent']['raw'])
        print(uniandino_proof_object['requested_proof']['revealed_attrs']['attr2_referent']['raw'])
        print(uniandino_proof_object['requested_proof']['revealed_attrs']['attr1_referent']['raw'])

        if type_of_user == 3:
            assert 'employee' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']   
        elif type_of_user == 2: 
            assert 'teacher' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']
        elif type_of_user == 1: 
            assert 'student' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']    
        else:
            assert 'invited' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']

        assert '54321' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr3_referent']['raw']
        assert 'Joven' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr2_referent']['raw']
        assert 'Susan' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr1_referent']['raw']


        assert await anoncreds.verifier_verify_proof(entry['uniandino_proof_request'], entry['uniandino_proof'],
                                                 entry['schemas_for_uniandino'],
                                                 entry['cred_defs_for_uniandino'],
                                                 entry['revoc_ref_defs_for_uniandino'],
                                                 entry['revoc_regs_for_uniandino']), "Credential dennied"   

        logger.info("==============================")
        logger.info("== Credential accepted ==")
        logger.info("------------------------------")   
        
        if type_of_event == 1:
            print("Revoking credential in 15 seconds")
            time.sleep(15)
            await cred_revocation()
        
    """
    Proves the Uniandino credential provided by the user. 
    If the attributes of the credential are proved and the credential has not been revoked, the credential is accepted
    """
    async def get_sicua():

        logger.info("==============================")
        logger.info("== Trying to get access to Sicua - Uniandino proving ==")
        logger.info("------------------------------")

        logger.info("\"Sicua\" -> Create \"Uniandino\" Proof Request")
        nonce = await anoncreds.generate_nonce()
        sicua['uniandino_proof_request'] = json.dumps({
            'nonce': nonce,
            'name': 'Uniandino',
            'version': '0.1',
            'self_attested_attributes': {},
            'requested_attributes': {
                'attr1_referent': {
                    'name': 'first_name',
                    'restrictions': [{'cred_def_id': uniandes['uniandino_cred_def_id']}]
                },
                'attr2_referent': {
                    'name': 'last_name',
                    'restrictions': [{'cred_def_id': uniandes['uniandino_cred_def_id']}]
                },
                'attr3_referent': {
                    'name': 'id',
                    'restrictions': [{'cred_def_id': uniandes['uniandino_cred_def_id']}]
                }, 
                'attr4_referent': {
                    'name': 'status',
                    'restrictions': [{'cred_def_id': uniandes['uniandino_cred_def_id']}]
                }
                   
            },
            'requested_predicates':{},
            'non_revoked': {'to': int(time.time())}   
        })

        logger.info("\"Sicua\" -> Send \"Uniandino\" Proof Request to "+ user['name'])
        user['uniandino_proof_request'] = sicua['uniandino_proof_request']

        logger.info("\""+user['name']+ "\" -> Get credentials for \"Uniandino\" Proof Request")

        search_for_uniandino_proof_request = \
            await anoncreds.prover_search_credentials_for_proof_req(user['wallet'],
                                                                user['uniandino_proof_request'], None)

        cred_for_attr1 = await get_credential_for_referent(search_for_uniandino_proof_request, 'attr1_referent')
        cred_for_attr2 = await get_credential_for_referent(search_for_uniandino_proof_request, 'attr2_referent')
        cred_for_attr3 = await get_credential_for_referent(search_for_uniandino_proof_request, 'attr3_referent')
        cred_for_attr4 = await get_credential_for_referent(search_for_uniandino_proof_request, 'attr4_referent')

        await anoncreds.prover_close_credentials_search_for_proof_req(search_for_uniandino_proof_request)
        logger.info(cred_for_attr1)
        user['creds_for_uniandino_proof'] = {cred_for_attr1['referent']: cred_for_attr1,
                                                cred_for_attr2['referent']: cred_for_attr2,
                                                cred_for_attr3['referent']: cred_for_attr3,
                                                cred_for_attr4['referent']: cred_for_attr4
                                                }
                            
        requested_timestamp = int(json.loads(sicua['uniandino_proof_request'])['non_revoked']['to'])

        print(user['pool'])
        print(user['did'])
        print(user['creds_for_uniandino_proof'])
        print(user['name'])
        print(requested_timestamp)

        user['schemas_for_uniandino'], user['cred_defs_for_uniandino'], \
        user['revoc_states_for_uniandino'] = \
            await prover_get_entities_from_ledger(user['pool'], user['did'],
                                                user['creds_for_uniandino_proof'], user['name'], None, requested_timestamp)

        logger.info("\""+user['name']+ "\" -> Create \"Uniandino\" Proof")

        revoc_states_for_uniandino = json.loads(user['revoc_states_for_uniandino'])
        timestamp_for_attr1 = get_timestamp_for_attribute(cred_for_attr1, revoc_states_for_uniandino)
        timestamp_for_attr2 = get_timestamp_for_attribute(cred_for_attr2, revoc_states_for_uniandino)
        timestamp_for_attr3 = get_timestamp_for_attribute(cred_for_attr3, revoc_states_for_uniandino)
        timestamp_for_attr4 = get_timestamp_for_attribute(cred_for_attr4, revoc_states_for_uniandino)
        
    
        user['uniandino_requested_creds'] = json.dumps({
            'self_attested_attributes': {},
                
            'requested_attributes': {
                'attr1_referent': {'cred_id': cred_for_attr1['referent'], 'revealed': True, 'timestamp': timestamp_for_attr1},
                'attr2_referent': {'cred_id': cred_for_attr2['referent'], 'revealed': True, 'timestamp': timestamp_for_attr2},
                'attr3_referent': {'cred_id': cred_for_attr3['referent'], 'revealed': True, 'timestamp': timestamp_for_attr3},
                'attr4_referent': {'cred_id': cred_for_attr4['referent'], 'revealed': True, 'timestamp': timestamp_for_attr4}
                
            },
            'requested_predicates':{}
        })
        
        user['uniandino_proof'] = \
            await anoncreds.prover_create_proof(user['wallet'], user['uniandino_proof_request'],
                                                user['uniandino_requested_creds'], user['master_secret_id'],
                                                user['schemas_for_uniandino'],
                                                user['cred_defs_for_uniandino'],
                                                user['revoc_states_for_uniandino'])

        logger.info("\""+user['name']+ "\" -> Send \"Uniandino\" Proof to Sicua")
        sicua['uniandino_proof'] = user['uniandino_proof']

        uniandino_proof_object = json.loads(sicua['uniandino_proof'])
            
        logger.info("\"Sicua\" -> Get Schemas, Credential Definitions and Revocation Registries from Ledger"
                        " required for Proof verifying")

        sicua['schemas_for_uniandino'], sicua['cred_defs_for_uniandino'], \
        sicua['revoc_ref_defs_for_uniandino'], sicua['revoc_regs_for_uniandino'] = \
            await verifier_get_entities_from_ledger(sicua['pool'], sicua['did'],
                                                    uniandino_proof_object['identifiers'], sicua['name'], requested_timestamp)

        logger.info("\"Sicua\" -> Verify \"Uniandino\" Proof from "+ user['name'])

        print( uniandino_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw'])
        print(uniandino_proof_object['requested_proof']['revealed_attrs']['attr3_referent']['raw'])
        print(uniandino_proof_object['requested_proof']['revealed_attrs']['attr2_referent']['raw'])
        print(uniandino_proof_object['requested_proof']['revealed_attrs']['attr1_referent']['raw'])

        if type_of_user == 1:
            assert 'student' ==  uniandino_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']
        else:
            assert 'teacher' ==  uniandino_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']

        assert '54321' ==  uniandino_proof_object['requested_proof']['revealed_attrs']['attr3_referent']['raw']
        assert 'Joven' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr2_referent']['raw']
        assert 'Susan' == uniandino_proof_object['requested_proof']['revealed_attrs']['attr1_referent']['raw']

        assert await anoncreds.verifier_verify_proof(sicua['uniandino_proof_request'], sicua['uniandino_proof'],
                                                 sicua['schemas_for_uniandino'],
                                                 sicua['cred_defs_for_uniandino'],
                                                 sicua['revoc_ref_defs_for_uniandino'],
                                                 sicua['revoc_regs_for_uniandino'])

        logger.info("==============================")
        logger.info("== Credential accepted ==")
        logger.info("------------------------------")

    """
    Creation of credential revocation when the user is an 'invited' and the type of event is the #1
    After the credential has been revoked, the proving of attributes will fail 
    """    

    async def cred_revocation():

        logger.info("==============================")

        logger.info("==============================")
        logger.info("== Credential revocation - Uniandes revokes"+ user['name'] +"'s Uniandino  ==")
        logger.info("------------------------------")

        logger.info("\"Uniandes\" - Revoke  credential")
        uniandes['user_cert_rev_reg_delta'] = \
            await anoncreds.issuer_revoke_credential(uniandes['wallet'],
                                                    uniandes['blob_storage_reader_cfg_handle'],
                                                    uniandes['revoc_reg_id'],
                                                    uniandes['uniandino_cred_rev_id'])

        logger.info("\"Uniandes\" - Post RevocationRegistryDelta to Ledger")
        uniandes['revoc_reg_entry_req'] = \
            await ledger.build_revoc_reg_entry_request(uniandes['did'], uniandes['revoc_reg_id'], 'CL_ACCUM',
                                                    uniandes['user_cert_rev_reg_delta'])
        await ledger.sign_and_submit_request(uniandes['pool'], uniandes['wallet'], uniandes['did'], uniandes['revoc_reg_entry_req'])
        
        
        logger.info("==============================")
        logger.info("== Time ==")
        logger.info("------------------------------") 

        await get_into()
            
    
    
    """
    Verification of service: sicua or campus
    """
    if type_of_service == 1:
        await get_sicua()
    else:
        await get_into()    
        







"""
Methods provided by Hyperledger Indy as a complement for the creation of credentials
"""

parser = argparse.ArgumentParser(description='Run python getting-started scenario (Alice/Faber)')
parser.add_argument('-t', '--storage_type', help='load custom wallet storage plug-in')
parser.add_argument('-l', '--library', help='dynamic library to load for plug-in')
parser.add_argument('-e', '--entrypoint', help='entry point for dynamic library')
parser.add_argument('-c', '--config', help='entry point for dynamic library')
parser.add_argument('-s', '--creds', help='entry point for dynamic library')

args = parser.parse_args()

# check if we need to dyna-load a custom wallet storage plug-in
if args.storage_type:
    if not (args.library and args.entrypoint):
        parser.print_help()
        sys.exit(0)
    stg_lib = CDLL(args.library)
    result = stg_lib[args.entrypoint]()
    if result != 0:
        print("Error unable to load wallet storage", result)
        parser.print_help()
        sys.exit(0)

    # for postgres storage, also call the storage init (non-standard)
    if args.storage_type == "postgres_storage":
        try:
            print("Calling init_storagetype() for postgres:", args.config, args.creds)
            init_storagetype = stg_lib["init_storagetype"]
            c_config = c_char_p(args.config.encode('utf-8'))
            c_credentials = c_char_p(args.creds.encode('utf-8'))
            result = init_storagetype(c_config, c_credentials)
            print(" ... returns ", result)
        except RuntimeError as e:
            print("Error initializing storage, ignoring ...", e)

    print("Success, loaded wallet storage", args.storage_type)

async def create_wallet(identity):
    logger.info("\"{}\" -> Create wallet".format(identity['name']))
    try:
        await wallet.create_wallet(wallet_config("create", identity['wallet_config']),
                                   wallet_credentials("create", identity['wallet_credentials']))
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    identity['wallet'] = await wallet.open_wallet(wallet_config("open", identity['wallet_config']),
                                                  wallet_credentials("open", identity['wallet_credentials']))
def wallet_config(operation, wallet_config_str):
    if not args.storage_type:
        return wallet_config_str
    wallet_config_json = json.loads(wallet_config_str)
    wallet_config_json['storage_type'] = args.storage_type
    if args.config:
        wallet_config_json['storage_config'] = json.loads(args.config)
    # print(operation, json.dumps(wallet_config_json))
    return json.dumps(wallet_config_json)


def wallet_credentials(operation, wallet_credentials_str):
    if not args.storage_type:
        return wallet_credentials_str
    wallet_credentials_json = json.loads(wallet_credentials_str)
    if args.creds:
        wallet_credentials_json['storage_credentials'] = json.loads(args.creds)
    return json.dumps(wallet_credentials_json)

async def getting_verinym(from_, to):
    await create_wallet(to)

    (to['did'], to['key']) = await did.create_and_store_my_did(to['wallet'], "{}")

    from_['info'] = {
        'did': to['did'],
        'verkey': to['key'],
        'role': to['role'] or None
    }

    await send_nym(from_['pool'], from_['wallet'], from_['did'], from_['info']['did'],
                   from_['info']['verkey'], from_['info']['role'])

async def send_nym(pool_handle, wallet_handle, _did, new_did, new_key, role):
    nym_request = await ledger.build_nym_request(_did, new_did, new_key, None, role)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, nym_request)

async def send_schema(pool_handle, wallet_handle, _did, schema):
    schema_request = await ledger.build_schema_request(_did, schema)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, schema_request)

async def get_schema(pool_handle, _did, schema_id):
    logger.info(schema_id)
    get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
    logger.info("REQUEST")
    logger.info(get_schema_request)
    get_schema_response = await ensure_previous_request_applied(
        pool_handle, get_schema_request, lambda response: response['result']['data'] is not None)
    logger.info("RESPONSE")
    logger.info(get_schema_response)
    logger.info(ledger.parse_get_schema_response(get_schema_response))
    return await ledger.parse_get_schema_response(get_schema_response)

async def ensure_previous_request_applied(pool_handle, checker_request, checker):
    for _ in range(3):
        response = json.loads(await ledger.submit_request(pool_handle, checker_request))
        try:
            if checker(response):
                return json.dumps(response)
        except TypeError:
            pass
        time.sleep(5)

async def send_cred_def(pool_handle, wallet_handle, _did, cred_def_json):
    cred_def_request = await ledger.build_cred_def_request(_did, cred_def_json)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, cred_def_request)

async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = \
        await ensure_previous_request_applied(pool_handle, get_cred_def_request,
                                              lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)

async def get_credential_for_referent(search_handle, referent):
    credentials = json.loads(
        await anoncreds.prover_fetch_credentials_for_proof_req(search_handle, referent, 10))
    return credentials[0]['cred_info']


def get_timestamp_for_attribute(cred_for_attribute, revoc_states):
    if cred_for_attribute['rev_reg_id'] in revoc_states:
        return int(next(iter(revoc_states[cred_for_attribute['rev_reg_id']])))
    else:
        return None
        
async def prover_get_entities_from_ledger(pool_handle, _did, identifiers, actor, timestamp_from=None,
                                          timestamp_to=None):
    schemas = {}
    cred_defs = {}
    rev_states = {}
    print(identifiers.values())
    for item in identifiers.values():
        logger.info("ITEMMM")
        logger.info(item)
        logger.info("\"{}\" -> Get Schema from Ledger".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        logger.info("\"{}\" -> Get Claim Definition from Ledger".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_id' in item and item['rev_reg_id'] is not None:
            # Create Revocations States
            logger.info("\"{}\" -> Get Revocation Registry Definition from Ledger".format(actor))
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(_did, item['rev_reg_id'])

            get_revoc_reg_def_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_def_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_def_json) = await ledger.parse_get_revoc_reg_def_response(get_revoc_reg_def_response)

            logger.info("\"{}\" -> Get Revocation Registry Delta from Ledger".format(actor))
            if not timestamp_to: timestamp_to = int(time.time())
            get_revoc_reg_delta_request = \
                await ledger.build_get_revoc_reg_delta_request(_did, item['rev_reg_id'], timestamp_from, timestamp_to)
            get_revoc_reg_delta_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_delta_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_delta_json, t) = \
                await ledger.parse_get_revoc_reg_delta_response(get_revoc_reg_delta_response)

            tails_reader_config = json.dumps(
                {'base_dir': dirname(json.loads(revoc_reg_def_json)['value']['tailsLocation']),
                 'uri_pattern': ''})
            blob_storage_reader_cfg_handle = await blob_storage.open_reader('default', tails_reader_config)

            logger.info('%s - Create Revocation State', actor)
            rev_state_json = \
                await anoncreds.create_revocation_state(blob_storage_reader_cfg_handle, revoc_reg_def_json,
                                                        revoc_reg_delta_json, t, item['cred_rev_id'])
            rev_states[rev_reg_id] = {t: json.loads(rev_state_json)}

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_states)

async def verifier_get_entities_from_ledger(pool_handle, _did, identifiers, actor, timestamp=None):
    schemas = {}
    cred_defs = {}
    rev_reg_defs = {}
    rev_regs = {}
    for item in identifiers:
        logger.info("\"{}\" -> Get Schema from Ledger".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        logger.info("\"{}\" -> Get Claim Definition from Ledger".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_id' in item and item['rev_reg_id'] is not None:
            # Get Revocation Definitions and Revocation Registries
            logger.info("\"{}\" -> Get Revocation Definition from Ledger".format(actor))
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(_did, item['rev_reg_id'])

            get_revoc_reg_def_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_def_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_def_json) = await ledger.parse_get_revoc_reg_def_response(get_revoc_reg_def_response)

            logger.info("\"{}\" -> Get Revocation Registry from Ledger".format(actor))
            if not timestamp: timestamp = item['timestamp']
            get_revoc_reg_request = \
                await ledger.build_get_revoc_reg_request(_did, item['rev_reg_id'], timestamp)
            get_revoc_reg_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, rev_reg_json, timestamp2) = await ledger.parse_get_revoc_reg_response(get_revoc_reg_response)

            rev_regs[rev_reg_id] = {timestamp2: json.loads(rev_reg_json)}
            rev_reg_defs[rev_reg_id] = json.loads(revoc_reg_def_json)

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_reg_defs), json.dumps(rev_regs)
