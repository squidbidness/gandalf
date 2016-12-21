#ifndef VECTOR_HPP_DA39A3EE
#define VECTOR_HPP_DA39A3EE

#include <boost/hana.hpp>

#include <algorithm>
#include <array>
#include <initializer_list>

namespace geo::hidden_Vector {
	using namespace boost::hana::literals;
}

namespace geo::hidden_Vector::exposed {

	template< typename T, size_t N >
	struct Vector : std::array<T, N> {

		using Base = std::array<T, N>;

		using Base::operator [];

		template< int I >
		constexpr T &operator[](
				std::integral_constant< int, I >
				)
		{
			return std::get<I>( *this );
		}
		template< int I >
		constexpr T const &operator[](
				std::integral_constant< int, I > i_c
				)
		{
			return (*this)[i_c];
		}

		constexpr T &x() {
			static_assert( N > 0 );
			return (*this)[0_c];
		}
		constexpr T const &x() const {
			return x();
		}

		constexpr T &y() {
			static_assert( N > 1 );
			return (*this)[1_c];
		}
		constexpr T const &y() const {
			return y();
		}

		constexpr T &z() {
			static_assert( N > 2 );
			return (*this)[2_c];
		}
		constexpr T const &z() const {
			return z();
		}

		constexpr T &w() {
			static_assert( N > 3 );
			return (*this)[3_c];
		}
		constexpr T const &w() const {
			return w();
		}

	};

	template< typename ...T >
	constexpr auto makeVector( T &&...t ) {
		return Vector< std::common_type_t<T...>, sizeof...(T) >{
				std::forward<T>( t )... };
	}


	template<
			typename ComponentOp,
			typename T,
			typename ...Ts,
			size_t N,
			size_t ...Ns,
			size_t ...I
			>
	requires requires( ComponentOp op, T t, Ts ...ts ) {
		requires ( (N == Ns) && ... );
		operation( std::forward<T>( t ), std::forward<Ts>( ts )... );
	}
	void forEachComponent(
			ComponentOp operation,
			Vector<T, N> const &v,
			Vector<Ts, Ns> const &...vs,
			std::integer_sequence< int, I... >
					= std::make_integer_sequence< int, sizeof...(vs) >()
			)
	{
		(
			operation(
					v[std::integral_constant< int, I >()],
					vs[std::integral_constant< int, I >()]...
					),
			...
			);
	}

	template< size_t N, size_t M >
	requires N == M
	auto dot( Vector< auto, N > const &a, Vector< auto, M > const &b ) {
		using Sum = decltype( a[0_c] + b[0_c] );
		Sum sum = 0;
		forEachComponent(
				[&sum] ( auto s, auto t ) { sum += s * t; },
				a,
				b
				);
		return sum;
	}


	template< size_t N > using VectorF = Vector<float, N>;
	template< size_t N > using VectorD = Vector<double, N>;

	template< typename T > using Vector1 = Vector<T, 1>;
	template< typename T > using Vector2 = Vector<T, 2>;
	template< typename T > using Vector3 = Vector<T, 3>;
	template< typename T > using Vector4 = Vector<T, 4>;

	using VectorF1 = VectorF<1>;
	using VectorF2 = VectorF<2>;
	using VectorF3 = VectorF<3>;
	using VectorF4 = VectorF<4>;

	using VectorD1 = VectorD<1>;
	using VectorD2 = VectorD<2>;
	using VectorD3 = VectorD<3>;
	using VectorD4 = VectorD<4>;

	namespace Vector_shorthand {
		constexpr auto V_( auto &&...t ) {
			return makeVector( std::forward<decltype(t)>( t )... );
		};
	}
}

namespace geo {
	using namespace hidden_Vector::exposed;
}

#endif
