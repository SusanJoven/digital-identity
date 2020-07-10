"""
 Identidad Digital basada en Blockchain para Instituciones Educativas (v1.0) con Hyperledger Indy (v1.15.0)
 Creación de identidad digital para miembros de la Universidad de los Andes (2020)
 Autora: Susan Paola Joven Vásquez

"""

import time

from src import connect_pool
from src.utils import run_coroutine


async def main():
    await connect_pool.run()
   

if __name__ == '__main__':
    run_coroutine(main)
    time.sleep(1)  # FIXME waiting for libindy thread complete
