#######################################################################################
# Libraries
import logging
import os
from datetime import datetime
import numpy as np
import xarray as xr
import rioxarray
import gzip
import pandas as pd

from copy import deepcopy

import matplotlib.pylab as plt
#######################################################################################


# --------------------------------------------------------------------------------
def load_monthly_avg_data_from_geotiff(da_domain_in,period_daily, period_monthly,
                                       folder_in, filename_in, template,
                                       aggregation_method, check_range, range,
                                       check_climatology_max, path_climatology_max_in, threshold_climatology_max,
                                       multidaily_cumulative, number_days_cumulative):

    # Load daily data and compute monthly means at the end of each month
    data_month_values = np.zeros(
        shape=(da_domain_in.shape[0], da_domain_in.shape[1])) * np.nan  # initialize container for monthly cumulative values
    data_month_values_ALL = np.zeros(shape=(da_domain_in.shape[0], da_domain_in.shape[1],
                                            period_monthly.__len__())) * np.nan  # initialize container for monthly cumulative values

    for time_i, time_date in enumerate(period_daily):

        # load data
        if multidaily_cumulative:
            # if multidaily_cumulative is true, we loop FORWARD for number_days_cumulative days in search of the data.
            period_search = pd.date_range(pd.to_datetime(time_date),
                                          pd.to_datetime(time_date) + pd.DateOffset(days=number_days_cumulative - 1),
                                          freq="D")

            for time_i_search, time_date_search in enumerate(period_search):

                logging.info(' --> Searching ' + time_date.strftime("%Y-%m-%d %H:%M") + ' over '+ str(number_days_cumulative) + ' days ...')

                path_data = os.path.join(folder_in, filename_in)
                tag_filled = {'source_gridded_P_sub_path_time': time_date_search,
                              'source_gridded_P_datetime': time_date_search,
                              'source_gridded_PET_sub_path_time': time_date_search,
                              'source_gridded_PET_datetime': time_date_search}
                path_data = fill_tags2string(path_data, template, tag_filled)
                if os.path.isfile(path_data):
                    logging.info(' --> Found cumulative for ' + time_date.strftime("%Y-%m-%d %H:%M") + ' at ' +  path_data)
                    break

                # if we DO NOT FIND any data, we can leave path_data wit the last time_date_search, as later
                # in this script we have another if os.path.isfile(path_data) that conditions all further steps

        else:
            # if multidaily_cumulative is false, we use time_date
            path_data = os.path.join(folder_in, filename_in)
            tag_filled = {'source_gridded_P_sub_path_time': time_date,
                          'source_gridded_P_datetime': time_date,
                          'source_gridded_PET_sub_path_time': time_date,
                          'source_gridded_PET_datetime': time_date}
            path_data = fill_tags2string(path_data, template, tag_filled)
            logging.info(' --> Looking for daily data at ' + path_data)

        if os.path.isfile(path_data):
            data_this_day = rioxarray.open_rasterio(path_data)
            data_this_day = np.squeeze(data_this_day)

            if multidaily_cumulative:
                data_this_day = data_this_day/number_days_cumulative
                logging.info(' --> Divided cumulative data by  ' + str(number_days_cumulative))


            #resampling
            if data_this_day.shape != da_domain_in.shape:
                coordinates_target = {
                    data_this_day.dims[0]: da_domain_in[da_domain_in.dims[0]].values,
                    data_this_day.dims[1]: da_domain_in[da_domain_in.dims[1]].values}
                data_this_day = data_this_day.interp(coordinates_target, method='nearest')
                logging.info(' --> Resampling ' + time_date.strftime("%Y-%m-%d %H:%M"))

            data_this_day_values = data_this_day.values

            # check range if needed
            if check_range:
                data_this_day_values[data_this_day_values < range[0]] = range[0]
                data_this_day_values[data_this_day_values > range[1]] = range[1]

            logging.info(' --> ' + time_date.strftime("%Y-%m-%d %H:%M") + ' loaded from ' + path_data)
        else:
            data_this_day_values = np.zeros(shape=(da_domain_in.shape[0], da_domain_in.shape[1])) * np.nan
            logging.warning(' ==> ' + time_date.strftime("%Y-%m-%d %H:%M") + ' not found!')

        # plt.figure()
        # plt.imshow(data_this_day_values)
        # plt.savefig('data_this_day_values.png')
        # plt.close()

        # accumulate monthly values
        data_month_values = np.nansum(np.dstack((data_month_values, data_this_day_values)),
                                      2)  # we add daily data to monthly cumulative ignoring nan

        # if end of month, save statistics and reset monthly cumulative matrix
        if time_date.is_month_end:
            if aggregation_method == 'mean':
                data_month_values = data_month_values / time_date.daysinmonth  # compute avg monthly stat
                logging.info(' --> Avg value computed for ' + time_date.strftime("%Y-%m-%d %H:%M"))
            elif aggregation_method == 'sum':
                data_month_values = data_month_values  # keep cumulative values
                logging.info(' --> Cum. value computed for ' + time_date.strftime("%Y-%m-%d %H:%M"))
            else:
                logging.error(' ===> Aggregation method not supported!')
                raise ValueError(' ===> Aggregation method not supported!')

            # check monthly climatology if needed
            if check_climatology_max:
                # load climatology layer
                tag_filled = {'source_gridded_P_sub_path_time': time_date,
                              'source_gridded_P_datetime': time_date,
                              'source_gridded_PET_sub_path_time': time_date,
                              'source_gridded_PET_datetime': time_date,
                              'source_gridded_climatology_P_datetime': time_date,
                              'source_gridded_climatology_PET_datetime': time_date}
                path_climatology = fill_tags2string(path_climatology_max_in, template, tag_filled)
                data_climatology = rioxarray.open_rasterio(path_climatology)
                data_climatology = np.squeeze(data_climatology)

                # regrid
                coordinates_target = {
                    data_climatology.dims[0]: da_domain_in[da_domain_in.dims[0]].values,
                    data_climatology.dims[1]: da_domain_in[da_domain_in.dims[1]].values}
                data_climatology = data_climatology.interp(coordinates_target, method='nearest')

                # set no data to NaN
                data_climatology.values[data_climatology.values == data_climatology.nodatavals[0]] = np.nan

                # plt.figure()
                # plt.imshow(data_climatology.values)
                # plt.colorbar()
                # plt.savefig(time_date.strftime("%m") + 'climatology.png')
                # plt.close()

                # apply threshold
                data_month_values[data_month_values > threshold_climatology_max*data_climatology.values] = np.nan

            data_month_values_ALL[:, :, period_monthly.get_loc(time_date)] = data_month_values
            logging.info(
                ' --> Monthly statistics stored in datacube at row ' + str(period_monthly.get_loc(time_date)))

            # plt.figure()
            # plt.imshow(data_month_values)
            # plt.colorbar()
            # plt.savefig(time_date.strftime("%Y%m%d") + 'cum.png')
            # plt.close()

            data_month_values = np.zeros(shape=(da_domain_in.shape[0], da_domain_in.shape[1])) * np.nan  # reset cumulative container

    data_ALL_da = create_darray_3d(data_month_values_ALL,
                                                period_monthly, da_domain_in['west_east'].values,
                                                da_domain_in['south_north'].values)
    return data_ALL_da


# --------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_3d(data, time, geo_x, geo_y, geo_1d=True,
                     coord_name_x='west_east', coord_name_y='south_north', coord_name_time='time',
                     dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x, dim_name_time]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={coord_name_time: (dim_name_time, time),
                                       coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)})
    else:
        logging.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da

# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_2d(data, geo_x, geo_y, geo_1d=True, name='geo',
                     coord_name_x='west_east', coord_name_y='south_north',
                     dim_name_x='west_east', dim_name_y='south_north',
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)},
                               name=name)
        data_da.name = name
    else:
        logging.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to add time in a unfilled string (path or filename)
def fill_tags2string(string_raw, tags_format=None, tags_filling=None):
    apply_tags = False
    if string_raw is not None:
        for tag in list(tags_format.keys()):
            if tag in string_raw:
                apply_tags = True
                break

    if apply_tags:

        tags_format_tmp = deepcopy(tags_format)
        for tag_key, tag_value in tags_format.items():
            tag_key_tmp = '{' + tag_key + '}'
            if tag_value is not None:
                if tag_key_tmp in string_raw:
                    string_filled = string_raw.replace(tag_key_tmp, tag_value)
                    string_raw = string_filled
                else:
                    tags_format_tmp.pop(tag_key, None)

        for tag_format_name, tag_format_value in list(tags_format_tmp.items()):

            if tag_format_name in list(tags_filling.keys()):
                tag_filling_value = tags_filling[tag_format_name]
                if tag_filling_value is not None:

                    if isinstance(tag_filling_value, datetime):
                        tag_filling_value = tag_filling_value.strftime(tag_format_value)

                    if isinstance(tag_filling_value, (float, int)):
                        tag_filling_value = tag_format_value.format(tag_filling_value)

                    string_filled = string_filled.replace(tag_format_value, tag_filling_value)

        string_filled = string_filled.replace('//', '/')
        return string_filled
    else:
        return string_raw


# -------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to unzip file
def unzip_filename(file_name_zip, file_name_unzip):

    file_handle_zip = gzip.GzipFile(file_name_zip, "rb")
    file_handle_unzip = open(file_name_unzip, "wb")

    file_data_unzip = file_handle_zip.read()
    file_handle_unzip.write(file_data_unzip)

    file_handle_zip.close()
    file_handle_unzip.close()

# --------------------------------------------------------------------------------