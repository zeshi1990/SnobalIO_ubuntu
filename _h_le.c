/*
 ** NAME
 **      _h_le -- calculates turbulent transfer at a point
 **
 ** SYNOPSIS
 **      #include "_snobal.h"
 **
 **      int
 **	_h_le(void)
 **
 ** DESCRIPTION
 **      Calculates point turbulent transfer (H and L_v_E) for a 2-layer
 **	snowcover.
 **
 ** GLOBAL VARIABLES READ
 **
 ** GLOBAL VARIABLES MODIFIED
 **
 */

#include "snobalio.h"
#include "_snobal.h"

int
_h_le(void)
{
	double  e_s;
	double	sat_vp;
	double	rel_z_T;  /* relative z_T (temperature measurement
			     height) above snow surface */
	double	rel_z_u;  /* relative z_u (windspeed measurement
			     height) above snow surface */

	/* calculate saturation vapor pressure */
	//	printf("-Ts0 %f Ta %f-", T_s_0, T_a);
	e_s = sati(T_s_0);
	if (e_s == FALSE) {
		printf("Saturation vapor pressure error");
		return FALSE;
	}


	/*** error check for bad vapor pressures ***/

	sat_vp = sati(T_a);
	if (sat_vp == FALSE) {
		printf("Bad vapor pressures");
		return FALSE;
	}
	if (e_a > sat_vp) {
		e_a = sat_vp;
	}

	/* determine relative measurement heights */
	if (relative_hts) {
		rel_z_T = z_T;
		rel_z_u = z_u;
	} else {
		rel_z_T = z_T - z_s;
		rel_z_u = z_u - z_s;
	}

	/* calculate H & L_v_E */

//	printf("Air pressure in Pa, %f\n", P_a);
//	printf("Air temp in K, %f\n", T_a);
//	printf("Snow surface temp in K, %f\n", T_s_0);
//	printf("Relative height of air temp in m, %f\n", rel_z_T);
//	printf("Air vapor pressure in Pa, %f\n", e_a);
//	printf("Vapor pressure at surface, %f\n", e_s);
//	printf("wind speed in m, %f\n", u);
//	printf("wind speed meausurement height in m, %f\n", rel_z_u);
//	printf("roughness length in m, %f\n", z_0);

	if (hle1 (P_a, T_a, T_s_0, rel_z_T, e_a, e_s, rel_z_T, u,
			rel_z_u, z_0, &H, &L_v_E, &E) != 0) {
		printf("error code is %d\n", hle1(P_a, T_a, T_s_0, rel_z_T, e_a, e_s, rel_z_T, u,
										  rel_z_u, z_0, &H, &L_v_E, &E));
		printf("hle1 did not converge\n");
		usrerr("hle1 did not converge\nP_a %f, T_a %f, T_s_0 %f\nrelative z_T %f, e_a %f, e_s %f\nu %f, relative z_u %f, z_0 %f\n", P_a, T_a, T_s_0, rel_z_T, e_a, e_s, u, rel_z_u, z_0);
		return FALSE;
	}

//	printf("Snow surface temp in K, %f\n", T_s_0);

	return TRUE;
}
