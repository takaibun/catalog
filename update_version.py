# -*- coding: utf-8 -*-
import json
import os
import datetime
import shutil
import yaml

base_path = os.path.dirname(os.path.abspath(__file__))
branchs = ['incubator','premium','stable','system']


current_date = datetime.datetime.now().strftime('%Y.%-m.%-d')
current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_apps(branch):
    return [x for x in os.listdir(os.path.join(base_path, branch)) if os.path.isdir(os.path.join(base_path, branch, x))]
def get_app_versions(branch, app):
    return [x for x in os.listdir(os.path.join(base_path, branch, app)) if os.path.isdir(os.path.join(base_path, branch, app, x))]

def sort_versions(versions):
    return sorted(versions, key=lambda x: [int(y) for y in x.split('.')])

def copy_version_to_current_date_version(branch, app, version):
    current_version_path = os.path.join(base_path, branch, app, version)
    current_date_version = current_date
    current_date_version_path = os.path.join(base_path, branch, app, current_date_version)
    shutil.copytree(current_version_path, current_date_version_path)

    with open(os.path.join(current_date_version_path, 'Chart.yaml'), 'r') as file:
        chart_data = yaml.safe_load(file)
        chart_data['version'] = current_date
        chart_data['appVersion'] = 'latest'

    with open(os.path.join(current_date_version_path, 'Chart.yaml'), 'w') as file:
        yaml.safe_dump(chart_data, file, default_flow_style=False)

    with open(os.path.join(current_date_version_path, 'ix_values.yaml'), 'r') as file:
        ix_values_data = yaml.safe_load(file)
        ix_values_data['image']['tag'] = 'rolling' if 'onedr0p' in ix_values_data['image']['repository'] else 'latest'
    with open(os.path.join(current_date_version_path, 'ix_values.yaml'), 'w') as file:
        yaml.safe_dump(ix_values_data, file, default_flow_style=False)

def delete_version(branch, app, version):
    shutil.rmtree(os.path.join(base_path, branch, app, version))
    app_versions_json_path = os.path.join(base_path, branch, app, 'app_versions.json')
    with open(app_versions_json_path, 'r') as file:
        app_versions_json = json.load(file)
        del app_versions_json[version]
    with open(app_versions_json_path, 'w') as file:
        json.dump(app_versions_json, file)


def add_current_date_version_to_app_version(branch, app, last_version):
    current_date_version = current_date
    app_versions_json_path = os.path.join(base_path, branch, app, 'app_versions.json')
    with open(app_versions_json_path, 'r') as file:
        app_versions_json = json.load(file)
        last_version = app_versions_json[last_version]
        app_versions_json[current_date_version] = last_version
        last_version = app_versions_json[current_date_version]
        last_version['version'] = current_date_version
        last_version['human_version'] = 'latest_{}'.format(current_date_version)
        last_version['chart_metadata']['appVersion'] = 'latest'
        last_version['chart_metadata']['version'] = current_date_version
        last_version['last_update'] = current_time
        location = last_version['location']
        parts = location.split('/')
        parts[-1] = current_date_version
        location = '/'.join(parts)
        last_version['location'] = location

    with open(app_versions_json_path, 'w') as file:
        json.dump(app_versions_json, file)


def update_catalog_json(branch, app):
    catalog_json_path = os.path.join(base_path, 'catalog.json')
    with open(catalog_json_path, 'r') as file:
        catalog_json = json.load(file)
        app = catalog_json[branch][app]
        app['latest_version'] = current_date
        app['latest_app_version'] = 'latest'
        app['latest_human_version'] = 'latest_{}'.format(current_date)
        app['last_update'] = current_time

    with open(catalog_json_path, 'w') as file:
        json.dump(catalog_json, file)


if __name__ == "__main__":
    for branch in branchs:
        for app in get_apps(branch):
            app_versions = get_app_versions(branch,app)
            app_versions = sort_versions(app_versions)
            copy_version_to_current_date_version(branch, app, app_versions[-1])
            add_current_date_version_to_app_version(branch, app, app_versions[-1])
            delete_version(branch, app, app_versions[0])
            update_catalog_json(branch, app)