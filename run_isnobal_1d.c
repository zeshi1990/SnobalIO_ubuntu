//
// Created by Zeshi Zheng on 3/21/17.
//

#include <h/snobal.h>
#include "snobalio.h"

double ** run_isnobal_1d(long length,
                         model_params * model_params1,
                         model_measure_params_1d * model_measure_params_1d1,
                         double ** model_states_1d1,
                         double ** model_climate_inputs_1d1,
                         double ** model_climate_inputs_1d2,
                         double ** model_precip_inputs_1d1) {

    const int n_states = 6;
//    const int n_climate_inputs = 6;
//    const int n_precip_inputs = 5;

    double ** states_results = (double **) malloc(sizeof(double *) * n_states);
    for (long j = 0; j < n_states; j++) {
        states_results[j] = (double *) malloc(sizeof(double) * length);
    }

    /*
     * Initialize model_measure_params1 and assign spatially static attributes
     */
    model_measure_params * model_measure_params1 = malloc(sizeof(model_measure_params));
    model_measure_params1->relative_hts = model_measure_params_1d1->relative_hts;
    model_measure_params1->z_g = model_measure_params_1d1->z_g;
    model_measure_params1->z_u = model_measure_params_1d1->z_u;
    model_measure_params1->z_T = model_measure_params_1d1->z_T;
    model_measure_params1->z_0 = model_measure_params_1d1->z_0;

    for (int i = 0; i < 6; i++) {
        for (long pix = 0; pix < 5; pix++) {
            printf("%f  ", model_states_1d1[i][pix]);
        }
        printf("\n");
    }

    for (int i = 0; i < 6; i++) {
        for (long pix = 0; pix < 5; pix++) {
            printf("%f  ", model_climate_inputs_1d1[i][pix]);
        }
        printf("\n");
    }

    for (int i = 0; i < 5; i++) {
        for (long pix = 0; pix < 5; pix++) {
            printf("%f  ", model_precip_inputs_1d1[i][pix]);
        }
        printf("\n");
    }


    for (long i = 0; i < length; i++) {
        /*
         *  Modify elevation attribute in model_measure_params1
         */
        model_measure_params1->elevation = model_measure_params_1d1->i_elevation[i];

        /*
         * Initialize following
         * model_states1,
         * model_climate_inputs1,
         * model_climate_inputs2,
         * model_precip_inputs1
         */
        model_states * model_states1 = malloc(sizeof(model_states));
        model_climate_inputs * model_climate_inputs1 = malloc(sizeof(model_climate_inputs));
        model_climate_inputs * model_climate_inputs2 = malloc(sizeof(model_climate_inputs));
        model_precip_inputs * model_precip_inputs1 = malloc(sizeof(model_precip_inputs));

        /*
         * Assign value to model_states1
         */
        model_states1->z_s = model_states_1d1[0][i];
        model_states1->rho = model_states_1d1[1][i];
        model_states1->T_s = model_states_1d1[2][i];
        model_states1->T_s_0 = model_states_1d1[3][i];
        model_states1->T_s_l = model_states_1d1[4][i];
        model_states1->h2o_sat = model_states_1d1[5][i];

        /*
         * Assign value to model_climate_inputs1
         */
        model_climate_inputs1->S_n = model_climate_inputs_1d1[0][i];
        model_climate_inputs1->I_lw = model_climate_inputs_1d1[1][i];
        model_climate_inputs1->T_a = model_climate_inputs_1d1[2][i];
        model_climate_inputs1->e_a = model_climate_inputs_1d1[3][i];
        model_climate_inputs1->u = model_climate_inputs_1d1[4][i];
        model_climate_inputs1->T_g = model_climate_inputs_1d1[5][i];


        /*
         * Assign value to model_climate_inputs2
         */
        model_climate_inputs2->S_n = model_climate_inputs_1d2[0][i];
        model_climate_inputs2->I_lw = model_climate_inputs_1d2[1][i];
        model_climate_inputs2->T_a = model_climate_inputs_1d2[2][i];
        model_climate_inputs2->e_a = model_climate_inputs_1d2[3][i];
        model_climate_inputs2->u = model_climate_inputs_1d2[4][i];
        model_climate_inputs2->T_g = model_climate_inputs_1d2[5][i];

        /*
         * Assign value to model_precip_inputs1
         */
        model_precip_inputs1->precip_now = (int) model_precip_inputs_1d1[0][i];
        model_precip_inputs1->m_pp = model_precip_inputs_1d1[1][i];
        model_precip_inputs1->percent_snow = model_precip_inputs_1d1[2][i];
        model_precip_inputs1->rho_snow = model_precip_inputs_1d1[3][i];
        model_precip_inputs1->T_pp = model_precip_inputs_1d1[4][i];

        /*
         * Please uncomment below when running
         */
        if (!snobal_init(model_params1, model_measure_params1,
                         model_states1, model_climate_inputs1,
                         model_climate_inputs2, model_precip_inputs1)) {
            printf("Initialization failed\n");
            states_results[0][i] = model_states1->z_s;
            states_results[1][i] = model_states1->rho;
            states_results[2][i] = model_states1->T_s;
            states_results[3][i] = model_states1->T_s_0;
            states_results[4][i] = model_states1->T_s_l;
            states_results[5][i] = model_states1->h2o_sat;
            continue;
        }

        init_snow();


        if(!do_data_tstep()) {
            printf("Oops! Something happened when running snobal, please check log files.\n");
            states_results[0][i] = model_states1->z_s;
            states_results[1][i] = model_states1->rho;
            states_results[2][i] = model_states1->T_s;
            states_results[3][i] = model_states1->T_s_0;
            states_results[4][i] = model_states1->T_s_l;
            states_results[5][i] = model_states1->h2o_sat;
            continue;
        };

        states_results[0][i] = z_s;
        states_results[1][i] = rho;
        states_results[2][i] = T_s;
        states_results[3][i] = T_s_0;
        states_results[4][i] = T_s_l;
        states_results[5][i] = h2o_sat;

        /*
         * free temporal objects
         */
        free(model_states1);
        free(model_climate_inputs1);
        free(model_climate_inputs2);
        free(model_precip_inputs1);

        if (i % 100 == 0) {
            printf("100th Iteration");
        }
    }

    printf("Finished one step\n");

    return states_results;

}