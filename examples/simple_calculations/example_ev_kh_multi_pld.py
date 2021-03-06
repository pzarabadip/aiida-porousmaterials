""" Sample run script for PorousMaterials Plugin"""
import os
import sys
import click
import pytest

from aiida.common import NotExistent
from aiida.orm import Code, Dict
from aiida.plugins import DataFactory
from aiida.engine import run, run_get_pk
from aiida_porousmaterials.calculations import PorousMaterialsCalculation

# Reading the structure and convert it to structure data.
SinglefileData = DataFactory('singlefile')  # pylint: disable=invalid-name
CifData = DataFactory('cif')  # pylint: disable=invalid-name

# Creating the command prompt input options using click


def example_ev_kh_multi_pld(julia_code, submit=True):
    """
    Test for Multi Comp PLD based with Kh
    """
    pwd = os.path.dirname(os.path.realpath(__file__))

    framework = CifData(file=os.path.join(pwd, 'files', 'HKUST1.cif')).store()

    acc_voronoi_nodes_xe = SinglefileData(
        file=os.path.join(pwd, 'files', 'xenon_probe', 'out.visVoro.voro_accessible')
    ).store()
    acc_voronoi_nodes_kr = SinglefileData(
        file=os.path.join(pwd, 'files', 'krypton_probe', 'out.visVoro.voro_accessible')
    ).store()
    acc_voronoi_nodes_pld = SinglefileData(file=os.path.join(pwd, 'files', 'pld_probe', 'out.visVoro.voro_accessible')
                                          ).store()
    data_path = os.path.join(pwd, 'data')
    parameters = Dict(
        dict={
            'data_path': data_path,
            'ff': 'UFF.csv',
            'cutoff': 12.5,
            'mixing': 'Lorentz-Berthelot',
            'framework': framework.filename,
            'frameworkname': framework.filename[:-4],
            'adsorbates': '["Xe","Kr"]',
            'temperature': 298.0,
            'input_template': 'ev_vdw_kh_multicomp_pld_template',
            'ev_setting': [99, 95, 90, 80, 50],  # if not defined the default is [90,80,50]
        }
    )
    voro_label_xe = framework.filename[:-4] + "_Xe"
    voro_label_kr = framework.filename[:-4] + "_Kr"
    voro_label_pld = framework.filename[:-4] + "_PLD"

    builder = PorousMaterialsCalculation.get_builder()
    builder.structure = {framework.filename[:-4]: framework}
    builder.parameters = parameters
    builder.acc_voronoi_nodes = {
        voro_label_xe: acc_voronoi_nodes_xe,
        voro_label_kr: acc_voronoi_nodes_kr,
        voro_label_pld: acc_voronoi_nodes_pld,
    }
    builder.code = julia_code
    builder.metadata.options.resources = { #pylint: disable = no-member
        'num_machines': 1,
        'num_mpiprocs_per_machine': 1,
    }
    builder.metadata.options.max_wallclock_seconds = 1 * 30 * 60  #pylint: disable = no-member
    builder.metadata.options.withmpi = False  #pylint: disable = no-member

    if submit:
        print('Testing PorousMaterials Ev for multi-component PLD probe...')
        res, pk = run_get_pk(builder)
        print('Ev Xe is: ', res['output_parameters'].dict.Xe['Xe_probe']['Ev_minimum'])
        print('Ev Kr is: ', res['output_parameters'].dict.Kr['Kr_probe']['Ev_minimum'])
        print('Ev Xe PLD is: ', res['output_parameters'].dict.Xe['PLD_probe']['Ev_minimum'])
        print('Ev Kr PLD is: ', res['output_parameters'].dict.Kr['PLD_probe']['Ev_minimum'])
        print('calculation pk: ', pk)
        print('OK, calculation has completed successfully')
        pytest.base_calc_pk = pk
    else:
        builder.metadata.dry_run = True  #pylint: disable = no-member
        builder.metadata.store_provenance = False  #pylint: disable = no-member
        run(builder)
        print('submission test successful')
        print("In order to actually submit, add '--submit'")


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='If true, actually submits the clac to the daemon.')
def cli(codelabel, submit):
    """Click interface"""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)
    example_ev_kh_multi_pld(code, submit)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
# EOF
